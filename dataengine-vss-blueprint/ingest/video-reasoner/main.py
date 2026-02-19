from opentelemetry import trace
from vast_runtime.vast_event import VastEvent  # type: ignore

from common.models import Settings, VideoReasoningResult
from common.clients import S3Client, CosmosReasoningClient, NemotronReasoningClient
from common.handler_utils import parse_s3_event, should_process_event


def init(ctx):
    """Initialize the serverless function"""
    with ctx.tracer.start_as_current_span("Video Reasoner Initialization"):
        settings = Settings.from_ctx_secrets(ctx.secrets)
        ctx.s3_client = S3Client(settings)
        
        # Select reasoning client based on provider
        provider = settings.reasoning_provider.lower()
        if provider == "nemotron":
            # Verify opencv-python is available for Nemotron
            try:
                import cv2
                import numpy as np
            except ImportError as e:
                raise RuntimeError(
                    f"opencv-python is required for Nemotron provider but is not installed. "
                    f"Please rebuild the function to install dependencies. Error: {e}"
                )
            ctx.reasoning_client = NemotronReasoningClient(settings)
            ctx.logger.info(f"[INIT] Using Nemotron provider: {settings.nemotron_model}")
        else:
            # Default to Cosmos
            ctx.reasoning_client = CosmosReasoningClient(settings)
            ctx.logger.info(f"[INIT] Using Cosmos provider: {settings.cosmos_model}")
        
        ctx.settings = settings


def handler(ctx, event: VastEvent):
    """Main handler function for vast serverless runtime"""
    
    with ctx.tracer.start_as_current_span("Video Reasoner Handler") as handler_span:
        try:
            data = event.get_data()
            event_type = getattr(event, 'get_type', lambda: 'element_trigger')()
            handler_span.set_attribute("event_type", event_type)
            
            with ctx.tracer.start_as_current_span("Event Parsing") as parse_span:
                event_info = parse_s3_event(data)
                bucket = event_info["bucket"]
                key = event_info["key"]
                event_name = event_info.get("event_name", "unknown")
                parse_span.set_attributes({
                    "bucket": bucket,
                    "key": key,
                    "event_name": event_name
                })
                ctx.logger.info(f"[INPUT] s3://{bucket}/{key} | event={event_name}")

            with ctx.tracer.start_as_current_span("Event Validation") as validation_span:
                should_process, skip_reason = should_process_event(key, event_name)
                if not should_process:
                    validation_span.set_attributes({"skip_reason": skip_reason})
                    ctx.logger.info(f"[SKIP] {key} | reason={skip_reason}")
                    return {"status": "skipped", "reason": skip_reason}
                
                validation_span.set_attributes({
                    "file_type": "mp4",
                    "supported": True
                })

            source = f"s3://{bucket}/{key}"
            filename = key.split('/')[-1] if '/' in key else key

            with ctx.tracer.start_as_current_span("S3 Download") as download_span:
                video_content = ctx.s3_client.download_file(bucket, key)
                size_mb = len(video_content) / (1024 * 1024)
                ctx.logger.info(f"[DOWNLOAD] {filename} | {size_mb:.2f}MB")
                download_span.set_attributes({
                    "bucket": bucket,
                    "key": key,
                    "file_size": len(video_content)
                })

            with ctx.tracer.start_as_current_span("Metadata Extraction") as metadata_span:
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
                    
                    camera_id = s3_metadata.get("camera-id", "")
                    capture_type = s3_metadata.get("capture-type", "")
                    neighborhood = s3_metadata.get("neighborhood", "")
                    
                    # Extract scenario from metadata, fall back to settings default
                    scenario = s3_metadata.get("scenario", "").strip()
                    if not scenario:
                        scenario = ctx.settings.scenario
                    
                    segment_number = int(segment_number_str) if segment_number_str else 0
                    total_segments = int(total_segments_str) if total_segments_str else 1
                    segment_duration = float(segment_duration_str) if segment_duration_str else 5.0
                    
                    ctx.logger.info(f"[METADATA] segment {segment_number}/{total_segments} | camera={camera_id or 'none'} | type={capture_type or 'none'} | area={neighborhood or 'none'} | scenario={scenario}")
                    
                    metadata_span.set_attributes({
                        "is_public": str(is_public),
                        "segment_number": segment_number,
                        "total_segments": total_segments,
                        "original_video": original_video,
                        "camera_id": camera_id,
                        "capture_type": capture_type,
                        "neighborhood": neighborhood,
                        "scenario": scenario
                    })
                except Exception as e:
                    ctx.logger.warning(f"[METADATA] Extraction failed, using defaults: {e}")
                    is_public = True
                    allowed_users = ""
                    tags = ""
                    upload_timestamp = ""
                    segment_number = 0
                    total_segments = 1
                    segment_duration = 5.0
                    original_video = filename
                    camera_id = ""
                    capture_type = ""
                    neighborhood = ""
                    scenario = ctx.settings.scenario  # Fall back to default from settings

            with ctx.tracer.start_as_current_span("Video Reasoning Analysis") as reasoning_span:
                provider = ctx.settings.reasoning_provider.lower()
                provider_name = "NEMOTRON" if provider == "nemotron" else "COSMOS"
                
                if provider == "nemotron":
                    ctx.logger.info(f"[{provider_name}] Starting analysis → {ctx.settings.nemotron_model} | scenario={scenario}")
                else:
                    ctx.logger.info(f"[{provider_name}] Starting analysis → {ctx.reasoning_client.settings.cosmos_host} | scenario={scenario}")
                
                reasoning_result = ctx.reasoning_client.analyze_video(video_content, filename, scenario=scenario)
                
                content_length = len(reasoning_result.get("reasoning_content", ""))
                tokens_used = reasoning_result.get("tokens_used", 0)
                processing_time = reasoning_result.get("processing_time", 0)
                model_name = reasoning_result.get("cosmos_model", "")
                
                reasoning_span.set_attributes({
                    "source": source,
                    "filename": filename,
                    "reasoning_provider": provider,
                    "reasoning_content_length": content_length,
                    "tokens_used": tokens_used,
                    "processing_time_seconds": processing_time,
                    "model": model_name,
                    "scenario": scenario
                })
                
                ctx.logger.info(f"[{provider_name}] Complete | {content_length} chars | {tokens_used} tokens | {processing_time:.2f}s")

            result = {
                "source": source,
                "filename": filename,
                "reasoning_content": reasoning_result["reasoning_content"],
                "cosmos_model": reasoning_result["cosmos_model"],
                "tokens_used": reasoning_result["tokens_used"],
                "processing_time": reasoning_result["processing_time"],
                "video_url": reasoning_result.get("video_url", ""),  # May be empty for Nemotron
                "status": "success",
                "reasoning_provider": ctx.settings.reasoning_provider.lower(),
                "is_public": is_public,
                "allowed_users": allowed_users,
                "tags": tags,
                "upload_timestamp": upload_timestamp,
                "segment_number": segment_number,
                "total_segments": total_segments,
                "segment_duration": segment_duration,
                "original_video": original_video,
                "camera_id": camera_id,
                "capture_type": capture_type,
                "neighborhood": neighborhood,
                "scenario": scenario
            }
            
            video_url_info = f" | video_url={reasoning_result.get('video_url', 'N/A')}" if reasoning_result.get("video_url") else ""
            ctx.logger.info(f"[COMPLETE] {filename} | segment {segment_number}/{total_segments} | provider={ctx.settings.reasoning_provider}{video_url_info}")
            return result
            
        except Exception as e:
            handler_span.set_attribute("error", True)
            handler_span.set_attribute("error.message", str(e))
            handler_span.record_exception(e)
            ctx.logger.error(f"Reasoning failed: {e}")
            return {"status": "error", "error": str(e)}

