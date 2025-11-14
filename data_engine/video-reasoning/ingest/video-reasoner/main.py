from opentelemetry import trace
from vast_runtime.vast_event import VastEvent  # type: ignore

from common.models import Settings, VideoReasoningResult
from common.clients import S3Client, CosmosReasoningClient
from common.handler_utils import parse_s3_event, should_process_event


def init(ctx):
    """Initialize the serverless function"""
    # ctx.logger.info("[INIT] Initializing video reasoner...")

    with ctx.tracer.start_as_current_span("Video Reasoner Initialization"):
        settings = Settings.from_ctx_secrets(ctx.secrets)
        # ctx.logger.info("[INIT] Settings configured successfully")
        # ctx.logger.info(f"[INIT] Cosmos host: {settings.cosmos_host}:{settings.cosmos_port}")
        # ctx.logger.info(f"[INIT] Cosmos URL: {settings.cosmos_url}")
        # ctx.logger.info(f"[INIT] SSH host: {settings.cosmos_ssh_host}")
        # ctx.logger.info(f"[INIT] Upload path: {settings.cosmos_upload_path}")
        
        ctx.s3_client = S3Client(settings)
        ctx.cosmos_client = CosmosReasoningClient(settings)
        
        # ctx.logger.info("[INIT] Video reasoner initialized successfully")


def handler(ctx, event: VastEvent):
    """Main handler function for vast serverless runtime"""
    
    try:
        data = event.get_data()
        # ctx.logger.info(f"[HANDLER] Video reasoning handler started - event type: {event.get_type()}")
        
        with ctx.tracer.start_as_current_span("Event Parsing") as parse_span:
            # ctx.logger.info("[PARSER] Parsing S3 event data")
            event_info = parse_s3_event(data)
            bucket = event_info["bucket"]
            key = event_info["key"]
            event_name = event_info.get("event_name", "unknown")
            parse_span.set_attributes({
                "bucket": bucket,
                "key": key,
                "event_name": event_name
            })
            # ctx.logger.info(f"[PARSER] Parsed event - bucket: {bucket}, key: {key}, event: {event_name}")

        with ctx.tracer.start_as_current_span("Event Validation") as validation_span:
            should_process, skip_reason = should_process_event(key, event_name)
            if not should_process:
                # ctx.logger.warning(f"[SKIP] Skipping event: {skip_reason}")
                validation_span.set_attributes({"skip_reason": skip_reason})
                return {"status": "skipped", "reason": skip_reason}
            
            validation_span.set_attributes({
                "file_type": "mp4",
                "supported": True
            })

        source = f"s3://{bucket}/{key}"
        filename = key.split('/')[-1] if '/' in key else key
        # ctx.logger.info(f"[HANDLER] Starting video reasoning analysis for {source}")

        with ctx.tracer.start_as_current_span("S3 Download") as download_span:
            ctx.logger.info(f"[S3] Downloading MP4 segment from {source}")
            video_content = ctx.s3_client.download_file(bucket, key)
            
            download_span.set_attributes({
                "bucket": bucket,
                "key": key,
                "file_size": len(video_content)
            })

        with ctx.tracer.start_as_current_span("Video Reasoning Analysis") as reasoning_span:
            ctx.logger.info("[COSMOS] Generating video reasoning with Cosmos")
            
            reasoning_result = ctx.cosmos_client.analyze_video(video_content, filename)
            
            content_length = len(reasoning_result.get("reasoning_content", ""))
            tokens_used = reasoning_result.get("tokens_used", 0)
            processing_time = reasoning_result.get("processing_time", 0)
            
            reasoning_span.set_attributes({
                "source": source,
                "filename": filename,
                "reasoning_content_length": content_length,
                "tokens_used": tokens_used,
                "processing_time_seconds": processing_time,
                "cosmos_model": reasoning_result.get("cosmos_model", ""),
                "cosmos_url": ctx.cosmos_client.cosmos_url,
                "video_url": reasoning_result.get("video_url", "")
            })
            
            ctx.logger.info(f"[COSMOS] Generated reasoning: {content_length} chars, {tokens_used} tokens, {processing_time:.2f}s")

        with ctx.tracer.start_as_current_span("Metadata Extraction") as metadata_span:
            ctx.logger.info("[METADATA] Extracting segment metadata from S3")
            try:
                head_response = ctx.s3_client.head_object(bucket=bucket, key=key)
                s3_metadata = head_response.get("Metadata", {})
                
                is_public_str = s3_metadata.get("is-public", "true")
                is_public = is_public_str.lower() == "true"
                allowed_users = s3_metadata.get("allowed-users", "")
                tags = s3_metadata.get("tags", "")
                upload_timestamp = s3_metadata.get("upload-timestamp", "")
                segment_number_str = s3_metadata.get("segment_number", "0")
                total_segments_str = s3_metadata.get("total_segments", "1")
                segment_duration_str = s3_metadata.get("segment_duration", "5.0")
                original_video = s3_metadata.get("original_video", filename)
                
                segment_number = int(segment_number_str) if segment_number_str else 0
                total_segments = int(total_segments_str) if total_segments_str else 1
                segment_duration = float(segment_duration_str) if segment_duration_str else 5.0
                
                allowed_users_count = len(allowed_users.split(",")) if allowed_users else 0
                
                metadata_span.set_attributes({
                    "is_public": str(is_public),
                    "allowed_users_count": allowed_users_count,
                    "tags": tags,
                    "segment_number": segment_number,
                    "total_segments": total_segments,
                    "segment_duration": segment_duration,
                    "original_video": original_video
                })
                
                ctx.logger.info(f"[METADATA] Extracted metadata - is_public: {is_public}, allowed_users: {allowed_users_count}, segment: {segment_number}/{total_segments}")
            except Exception as e:
                ctx.logger.warning(f"[METADATA] Failed to extract metadata: {e}. Using defaults.")
                is_public = True
                allowed_users = ""
                tags = ""
                upload_timestamp = ""
                segment_number = 0
                total_segments = 1
                segment_duration = 5.0
                original_video = filename

        result = {
            "source": source,
            "filename": filename,
            "reasoning_content": reasoning_result["reasoning_content"],
            "cosmos_model": reasoning_result["cosmos_model"],
            "tokens_used": reasoning_result["tokens_used"],
            "processing_time": reasoning_result["processing_time"],
            "video_url": reasoning_result["video_url"],
            "status": "success",
            "is_public": is_public,
            "allowed_users": allowed_users,
            "tags": tags,
            "upload_timestamp": upload_timestamp,
            "segment_number": segment_number,
            "total_segments": total_segments,
            "segment_duration": segment_duration,
            "original_video": original_video
        }
        
        ctx.logger.info(f"[SUCCESS] Video reasoning completed for {source}")
        return result
        
    except Exception as e:
        ctx.logger.error(f"[ERROR] Handler processing failed: {e}")
        return {"status": "error", "error": f"Handler processing failed: {e}"}

