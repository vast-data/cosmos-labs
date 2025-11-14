from opentelemetry import trace
from vast_runtime.vast_event import VastEvent  # type: ignore

from common.models import Settings, ReasoningEvent, EmbeddingResult
from common.embedding_client import EmbeddingClient
from common.handler_utils import parse_reasoning_event, validate_reasoning_content


def init(ctx):
    """Initialize the serverless function"""
    # ctx.logger.info("[INIT] Initializing reasoning embedder...")

    with ctx.tracer.start_as_current_span("Reasoning Embedder Initialization"):
        settings = Settings.from_ctx_secrets(ctx.secrets)
        # ctx.logger.info("[INIT] Settings configured successfully")
        
        ctx.embedding_client = EmbeddingClient(settings)
        ctx.settings = settings
        
        # ctx.logger.info(f"[INIT] Embedding model: {settings.embeddingmodel}")
        # ctx.logger.info(f"[INIT] Embedding dimensions: {settings.embeddingdimensions}")
        # ctx.logger.info("[INIT] Reasoning embedder initialized successfully")


def handler(ctx, event: VastEvent):
    """Main handler function for vast serverless runtime"""
    
    try:
        data = event.get_data()
        # ctx.logger.info(f"[HANDLER] Reasoning embedder handler started - event type: {event.get_type()}")
        
        with ctx.tracer.start_as_current_span("Reasoning Event Parsing") as parse_span:
            # ctx.logger.info("[PARSER] Parsing reasoning event data")
            
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
            
            allowed_users_count = len(allowed_users.split(",")) if allowed_users else 0
            
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
                "original_video": original_video
            })
            
            # ctx.logger.info(f"[PARSER] Parsed reasoning - filename: {filename}, content: {len(reasoning_content)} chars, segment: {segment_number}/{total_segments}")

        with ctx.tracer.start_as_current_span("Content Validation") as validation_span:
            if not validate_reasoning_content(reasoning_content):
                # ctx.logger.warning("[SKIP] No reasoning content to process")
                validation_span.set_attributes({"valid": False})
                return {"status": "skipped", "reason": "No reasoning content"}
            
            validation_span.set_attributes({"valid": True})

        with ctx.tracer.start_as_current_span("Embedding Generation") as embed_span:
            ctx.logger.info("[EMBEDDING] Generating embedding for reasoning text")
            
            embeddings = ctx.embedding_client.get_embeddings([reasoning_content])
            embedding = embeddings[0] if embeddings else []
            
            if not embedding:
                raise RuntimeError("Failed to generate embedding")
            
            embed_span.set_attributes({
                "embedding_dimensions": len(embedding),
                "embedding_model": ctx.settings.embeddingmodel,
                "embedding_host": ctx.settings.embeddinghost
            })
            
            ctx.logger.info(f"[EMBEDDING] Generated embedding with {len(embedding)} dimensions")

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
            "original_video": original_video
        }
        
        ctx.logger.info(f"[SUCCESS] Reasoning embedding completed - {len(embedding)} dims for segment {segment_number}/{total_segments}")
        
        return result
        
    except Exception as e:
        ctx.logger.error(f"[ERROR] Handler processing failed: {e}", exc_info=True)
        return {"status": "error", "error": f"Handler processing failed: {e}"}

