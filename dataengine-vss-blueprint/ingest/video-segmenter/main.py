from opentelemetry import trace
from vast_runtime.vast_event import VastEvent  # type: ignore

from common.models import Settings, S3ObjectMetadataModel
from common.video_processor import VideoProcessor
from common.handler_utils import (
    parse_s3_event, 
    should_process_event, 
    get_output_bucket_name, 
    get_segment_key, 
    prepare_metadata
)
from common.clients import S3Client


def init(ctx):
    """Initialize the serverless function"""
    with ctx.tracer.start_as_current_span("Video Segmenter Initialization"):
        settings = Settings.from_ctx_secrets(ctx.secrets)
        ctx.processor = VideoProcessor(settings)
        ctx.s3_client = S3Client(settings)


def handler(ctx, event: VastEvent):
    """Main handler function for vast serverless runtime"""
    
    with ctx.tracer.start_as_current_span("Video Segmenter Handler") as handler_span:
        try:
            data = event.get_data()
            event_type = getattr(event, 'get_type', lambda: 'element_trigger')()
            handler_span.set_attribute("event_type", event_type)
            
            with ctx.tracer.start_as_current_span("Event Parsing") as parse_span:
                event_info = parse_s3_event(data)
                bucket = event_info["bucket"]
                key = event_info["key"]
                event_name = event_info.get("event_name", "unknown")
                sequencer = event_info.get("sequencer", "")
                etag = event_info.get("etag", "")
                parse_span.set_attributes({
                    "bucket": bucket,
                    "key": key,
                    "event_name": event_name,
                    "sequencer": sequencer,
                    "etag": etag
                })
                ctx.logger.info(f"[INPUT] s3://{bucket}/{key} | event={event_name}")

            with ctx.tracer.start_as_current_span("Event Validation") as validation_span:
                should_process, skip_reason = should_process_event(key, event_name)
                if not should_process:
                    validation_span.set_attributes({"skip_reason": skip_reason})
                    ctx.logger.info(f"[SKIP] {key} | reason={skip_reason}")
                    return {"status": "skipped", "reason": skip_reason}
                
                file_extension = key.lower().split('.')[-1] if '.' in key else ''
                validation_span.set_attributes({
                    "file_extension": file_extension,
                    "supported_video": True
                })

            source = f"s3://{bucket}/{key}"
            filename = key.split('/')[-1] if '/' in key else key
            
            # Idempotency check: skip if already segmented
            output_bucket = get_output_bucket_name(bucket, ctx.processor.settings.output_bucket_suffix)
            segment_key = get_segment_key(filename, 1, 1)
            try:
                existing_segment = ctx.s3_client.head_object(bucket=output_bucket, key=segment_key)
                if existing_segment:
                    ctx.logger.info(f"[SKIP] {filename} already segmented in {output_bucket}")
                    return {
                        "status": "skipped", 
                        "reason": "Already segmented",
                        "source": source,
                        "output_bucket": output_bucket
                    }
            except Exception:
                pass

            with ctx.tracer.start_as_current_span("S3 Download") as download_span:
                video_content = ctx.s3_client.download_file(bucket, key)
                size_mb = len(video_content) / (1024 * 1024)
                ctx.logger.info(f"[DOWNLOAD] {filename} | {size_mb:.2f}MB | ext={file_extension}")
                download_span.set_attributes({
                    "bucket": bucket,
                    "key": key,
                    "file_size_bytes": len(video_content),
                    "file_extension": file_extension
                })

            with ctx.tracer.start_as_current_span("Metadata Extraction") as metadata_span:
                original_metadata = ctx.s3_client.head_object(bucket=bucket, key=key)
                raw_metadata = original_metadata.get("Metadata", {})
                s3_metadata = S3ObjectMetadataModel(**raw_metadata)
                
                is_public = s3_metadata.get_is_public_bool() if s3_metadata.is_public else True
                allowed_users = s3_metadata.get_allowed_users_list() if s3_metadata.allowed_users else []
                tags = s3_metadata.get_tags_list()
                
                # CLI/tool uploads default to public
                if not s3_metadata.is_public and not s3_metadata.allowed_users:
                    is_public = True
                    allowed_users = []
                
                scenario = s3_metadata.scenario or ""
                ctx.logger.info(f"[METADATA] public={is_public} | camera={s3_metadata.camera_id or 'none'} | type={s3_metadata.capture_type or 'none'} | area={s3_metadata.neighborhood or 'none'} | scenario={scenario or 'none'}")
                
                metadata_span.set_attributes({
                    "is_public": str(is_public),
                    "allowed_users_count": len(allowed_users),
                    "tags_count": len(tags),
                    "tags": ",".join(tags) if tags else "",
                    "source": source,
                    "filename": filename,
                    "camera_id": s3_metadata.camera_id or "",
                    "capture_type": s3_metadata.capture_type or "",
                    "neighborhood": s3_metadata.neighborhood or "",
                    "scenario": scenario
                })

            successful_uploads = 0
            failed_uploads = 0
            
            def upload_segment_callback(segment_info, original_filename):
                nonlocal successful_uploads, failed_uploads
                segment_content, segment_number, total_segments, duration, start_time, end_time = segment_info
                
                segment_key = get_segment_key(original_filename, segment_number, total_segments)
                segment_metadata = prepare_metadata(
                    original_metadata, segment_number, total_segments, duration, original_filename
                )
                
                if is_public and not allowed_users:
                    segment_metadata["is-public"] = "true"
                    segment_metadata["allowed-users"] = ""
                
                success = ctx.s3_client.upload_bytes(
                    segment_content, output_bucket, segment_key, segment_metadata
                )
                
                if success:
                    successful_uploads += 1
                else:
                    failed_uploads += 1
                    ctx.logger.error(f"Failed to upload segment {segment_number}/{total_segments}")

            with ctx.tracer.start_as_current_span("Video Segmentation and Upload") as video_span:
                ctx.processor.process_video_segments(video_content, filename, upload_segment_callback)
                total_segments = successful_uploads + failed_uploads
                
                video_span.set_attributes({
                    "segments_count": total_segments,
                    "segment_duration": ctx.processor.segment_duration,
                    "output_bucket": output_bucket,
                    "successful_uploads": successful_uploads,
                    "failed_uploads": failed_uploads
                })

            result = {
                "source": source,
                "original_video": filename,
                "file_type": file_extension,
                "segments_created": total_segments,
                "successful_uploads": successful_uploads,
                "failed_uploads": failed_uploads,
                "output_bucket": output_bucket,
                "segment_duration": ctx.processor.segment_duration,
                "status": "success"
            }
            
            ctx.logger.info(f"[COMPLETE] {filename} → {output_bucket} | {successful_uploads}/{total_segments} segments | {ctx.processor.segment_duration}s each")
            return result
            
        except Exception as e:
            handler_span.set_attribute("error", True)
            handler_span.set_attribute("error.message", str(e))
            handler_span.record_exception(e)
            ctx.logger.error(f"Segmentation failed: {e}")
            return {"status": "error", "error": str(e)}

