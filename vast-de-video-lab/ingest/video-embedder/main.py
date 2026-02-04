from opentelemetry import trace
from vast_runtime.vast_event import VastEvent  # type: ignore

from common.models import Settings, ReasoningEvent, EmbeddingResult
from common.embedding_client import EmbeddingClient
from common.handler_utils import parse_reasoning_event, validate_reasoning_content


def init(ctx):
    """Initialize the serverless function"""
    with ctx.tracer.start_as_current_span("Reasoning Embedder Initialization"):
        settings = Settings.from_ctx_secrets(ctx.secrets)
        ctx.embedding_client = EmbeddingClient(settings)
        ctx.settings = settings


def handler(ctx, event: VastEvent):
    """Main handler function for vast serverless runtime"""
    
    with ctx.tracer.start_as_current_span("Video Embedder Handler") as handler_span:
        try:
            data = event.get_data()
            event_type = getattr(event, 'get_type', lambda: 'element_trigger')()
            handler_span.set_attribute("event_type", event_type)
            
            with ctx.tracer.start_as_current_span("Reasoning Event Parsing") as parse_span:
                reasoning_event = parse_reasoning_event(data)
                
                source = reasoning_event.get("source", "")
                filename = reasoning_event.get("filename", "")
                reasoning_content = reasoning_event.get("reasoning_content", "")
                cosmos_model = reasoning_event.get("cosmos_model", "")
                tokens_used = reasoning_event.get("tokens_used", 0)
                processing_time = reasoning_event.get("processing_time", 0.0)
                video_url = reasoning_event.get("video_url", "")
                status = reasoning_event.get("status", "success")
                
                is_public = reasoning_event.get("is_public", True)
                allowed_users = reasoning_event.get("allowed_users", "")
                tags = reasoning_event.get("tags", "")
                upload_timestamp = reasoning_event.get("upload_timestamp", "")
                segment_number = reasoning_event.get("segment_number", 0)
                total_segments = reasoning_event.get("total_segments", 1)
                segment_duration = reasoning_event.get("segment_duration", 5.0)
                original_video = reasoning_event.get("original_video", filename)
                
                camera_id = reasoning_event.get("camera_id", "")
                capture_type = reasoning_event.get("capture_type", "")
                neighborhood = reasoning_event.get("neighborhood", "")
                scenario = reasoning_event.get("scenario", "")
                
                allowed_users_count = len(allowed_users.split(",")) if allowed_users else 0
                
                ctx.logger.info(f"[INPUT] {filename} | segment {segment_number}/{total_segments} | reasoning={len(reasoning_content)} chars")
                
                parse_span.set_attributes({
                    "source": source,
                    "filename": filename,
                    "cosmos_model": cosmos_model,
                    "tokens_used": tokens_used,
                    "processing_time": processing_time,
                    "status": status,
                    "reasoning_content_length": len(reasoning_content),
                    "is_public": str(is_public),
                    "allowed_users_count": allowed_users_count,
                    "segment_number": segment_number,
                    "total_segments": total_segments,
                    "tags": tags,
                    "original_video": original_video,
                    "camera_id": camera_id,
                    "capture_type": capture_type,
                    "neighborhood": neighborhood,
                    "scenario": scenario
                })

            with ctx.tracer.start_as_current_span("Content Validation") as validation_span:
                if not validate_reasoning_content(reasoning_content):
                    validation_span.set_attributes({"valid": False})
                    ctx.logger.info(f"[SKIP] {filename} | no reasoning content to embed")
                    return {"status": "skipped", "reason": "No reasoning content"}
                
                validation_span.set_attributes({"valid": True})

            with ctx.tracer.start_as_current_span("Embedding Generation") as embed_span:
                ctx.logger.info(f"[EMBED] Generating embedding via {ctx.settings.embeddingmodel}")
                embeddings = ctx.embedding_client.get_embeddings([reasoning_content])
                embedding = embeddings[0] if embeddings else []
                
                if not embedding:
                    raise RuntimeError("Failed to generate embedding - empty response from API")
                
                ctx.logger.info(f"[EMBED] Complete | {len(embedding)} dimensions")
                
                embed_span.set_attributes({
                    "embedding_dimensions": len(embedding),
                    "embedding_model": ctx.settings.embeddingmodel
                })

            result = {
                "source": source,
                "filename": filename,
                "reasoning_content": reasoning_content,
                "embedding": embedding,
                "embedding_model": ctx.settings.embeddingmodel,
                "embedding_dimensions": len(embedding),
                "cosmos_model": cosmos_model,
                "tokens_used": tokens_used,
                "processing_time": processing_time,
                "video_url": video_url,
                "status": "success",
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
            
            ctx.logger.info(f"[COMPLETE] {filename} | segment {segment_number}/{total_segments} | {len(embedding)} dims | metadata: camera={camera_id or 'none'}, type={capture_type or 'none'}")
            return result
            
        except Exception as e:
            handler_span.set_attribute("error", True)
            handler_span.set_attribute("error.message", str(e))
            handler_span.record_exception(e)
            ctx.logger.error(f"Embedding failed: {e}")
            return {"status": "error", "error": str(e)}

