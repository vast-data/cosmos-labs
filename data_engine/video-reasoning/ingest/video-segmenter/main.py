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
    # ctx.logger.info("[INIT] Initializing video segmenter...")

    with ctx.tracer.start_as_current_span("Video Segmenter Initialization"):
        settings = Settings.from_ctx_secrets(ctx.secrets)
        # ctx.logger.info("[INIT] Settings configured successfully")
        
        processor = VideoProcessor(settings)
        ctx.processor = processor
        ctx.s3_client = S3Client(settings)
        
        # ctx.logger.info("[INIT] Video segmenter initialized successfully")


def handler(ctx, event: VastEvent):
    """Main handler function for vast serverless runtime"""
    
    try:
        data = event.get_data()
        # ctx.logger.info(f"[HANDLER] Video segmentation handler started - event type: {event.get_type()}")
        
        with ctx.tracer.start_as_current_span("Event Parsing") as parse_span:
            # ctx.logger.info("[PARSER] Parsing S3 event data")
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
            # ctx.logger.info(f"[PARSER] Parsed event - bucket: {bucket}, key: {key}, event: {event_name}, sequencer: {sequencer}, etag: {etag}")

        with ctx.tracer.start_as_current_span("Event Validation") as validation_span:
            should_process, skip_reason = should_process_event(key, event_name)
            if not should_process:
                # ctx.logger.warning(f"[SKIP] Skipping event: {skip_reason}")
                validation_span.set_attributes({"skip_reason": skip_reason})
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
                # ctx.logger.info(f"[SKIP] Segments already exist for {source} in {output_bucket} - skipping (idempotent)")
                return {
                    "status": "skipped", 
                    "reason": "Already segmented",
                    "source": source,
                    "output_bucket": output_bucket
                }
        except Exception:
            pass
        
        # ctx.logger.info(f"[HANDLER] Starting video segmentation pipeline for {source} (detected extension: {file_extension})")

        with ctx.tracer.start_as_current_span("S3 Download") as download_span:
            ctx.logger.info(f"[S3] Downloading video from s3://{bucket}/{key}")
            video_content = ctx.s3_client.download_file(bucket, key)
            
            ctx.logger.info(f"[S3] Downloaded video file: {len(video_content)} bytes")
            
            download_span.set_attributes({
                "bucket": bucket,
                "key": key,
                "file_size_bytes": len(video_content),
                "file_extension": file_extension,
                "s3_endpoint": ctx.processor.settings.s3endpoint
            })

        with ctx.tracer.start_as_current_span("Metadata Extraction") as metadata_span:
            ctx.logger.info("[METADATA] Extracting S3 object metadata")
            
            original_metadata = ctx.s3_client.head_object(bucket=bucket, key=key)
            s3_metadata = S3ObjectMetadataModel(**original_metadata.get("Metadata", {}))
            
            is_public = s3_metadata.get_is_public_bool() if s3_metadata.is_public else True
            allowed_users = s3_metadata.get_allowed_users_list() if s3_metadata.allowed_users else []
            tags = s3_metadata.get_tags_list()
            
            # CLI/tool uploads default to public
            if not s3_metadata.is_public and not s3_metadata.allowed_users:
                is_public = True
                allowed_users = []
                ctx.logger.info("[METADATA] CLI/tool upload detected - defaulting to public access")
            
            metadata_span.set_attributes({
                "is_public": str(is_public),
                "allowed_users_count": len(allowed_users),
                "tags_count": len(tags),
                "tags": ",".join(tags) if tags else "",
                "source": source,
                "filename": filename
            })
            
            ctx.logger.info(f"[METADATA] Extracted metadata - is_public: {is_public}, allowed_users: {len(allowed_users)}, tags: {len(tags)}")

        successful_uploads = 0
        failed_uploads = 0
        
        def upload_segment_callback(segment_info, original_filename):
            nonlocal successful_uploads, failed_uploads
            segment_content, segment_number, total_segments, duration, start_time, end_time = segment_info
            
            segment_key = get_segment_key(original_filename, segment_number, total_segments)
            segment_metadata = prepare_metadata(
                original_metadata, 
                segment_number, 
                total_segments, 
                duration, 
                original_filename
            )
            
            if is_public and not allowed_users:
                segment_metadata["is-public"] = "true"
                segment_metadata["allowed-users"] = ""  # Empty string for CLI uploads
            
            success = ctx.s3_client.upload_bytes(
                segment_content, 
                output_bucket, 
                segment_key, 
                segment_metadata
            )
            
            if success:
                successful_uploads += 1
                ctx.logger.info(f"[S3] Uploaded segment {segment_number}/{total_segments} to s3://{output_bucket}/{segment_key}")
            else:
                failed_uploads += 1
                ctx.logger.error(f"[S3] Failed to upload segment {segment_number}/{total_segments} to s3://{output_bucket}/{segment_key}")

        with ctx.tracer.start_as_current_span("Video Segmentation and Upload") as video_span:
            ctx.logger.info(f"[SEGMENTATION] Processing video into {ctx.processor.segment_duration}s segments")
            
            segments = ctx.processor.process_video_segments(video_content, filename, upload_segment_callback)
            
            # When using callback, segments are not accumulated in memory
            total_segments = successful_uploads + failed_uploads
            ctx.logger.info(f"[SEGMENTATION] Processed {total_segments} video segments ({successful_uploads} successful, {failed_uploads} failed)")
            
            video_span.set_attributes({
                "segments_count": total_segments,
                "segment_duration": ctx.processor.segment_duration,
                "output_codec": ctx.processor.output_codec,
                "output_format": ctx.processor.output_format,
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
        
        ctx.logger.info(f"[SUCCESS] Video segmentation completed: {total_segments} segments from {source}")
        return result
        
    except Exception as e:
        ctx.logger.error(f"[ERROR] Handler processing failed: {e}")
        return {"status": "error", "error": f"Handler processing failed: {e}"}

