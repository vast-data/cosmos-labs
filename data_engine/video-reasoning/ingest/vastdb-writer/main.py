from opentelemetry import trace
from vast_runtime.vast_event import VastEvent  # type: ignore

from common.models import Settings, EmbeddingEvent
from common.vastdb_client import VastDBClient
from common.handler_utils import parse_embedding_event, validate_embedding


def init(ctx):
    """Initialize the serverless function"""
    # ctx.logger.info("[INIT] Initializing VastDB writer...")

    with ctx.tracer.start_as_current_span("VastDB Writer Initialization"):
        settings = Settings.from_ctx_secrets(ctx.secrets)
        # ctx.logger.info("[INIT] Settings configured successfully")
        
        ctx.vastdb_client = VastDBClient(settings)
        
        # ctx.logger.info(f"[INIT] VastDB: {settings.vdbbucket}.{settings.vdbschema}.{settings.vdbcollection}")
        # ctx.logger.info(f"[INIT] Vector dimensions: {settings.embeddingdimensions}")
        # ctx.logger.info("[INIT] VastDB writer initialized successfully")


def handler(ctx, event: VastEvent):
    """Main handler function for vast serverless runtime"""
    
    try:
        data = event.get_data()
        # ctx.logger.info(f"[HANDLER] VastDB writer handler started - event type: {event.get_type()}")
        
        with ctx.tracer.start_as_current_span("Embedding Event Parsing") as parse_span:
            # ctx.logger.info("[PARSER] Parsing embedding event data")
            
            embedding_event = parse_embedding_event(data)
            
            source = embedding_event.get("source", "")
            filename = embedding_event.get("filename", "")
            reasoning_content = embedding_event.get("reasoning_content", "")
            embedding = embedding_event.get("embedding", [])
            embedding_model = embedding_event.get("embedding_model", "")
            embedding_dimensions = embedding_event.get("embedding_dimensions", 0)
            status = embedding_event.get("status", "success")
            
            is_public = embedding_event.get("is_public")
            allowed_users = embedding_event.get("allowed_users")
            segment_number = embedding_event.get("segment_number")
            total_segments = embedding_event.get("total_segments")
            tags = embedding_event.get("tags", "")
            original_video = embedding_event.get("original_video", filename)
            
            allowed_users_count = len(allowed_users.split(",")) if allowed_users else 0
            
            parse_span.set_attributes({
                "source": source,
                "filename": filename,
                "embedding_model": embedding_model,
                "embedding_dimensions": embedding_dimensions,
                "status": status,
                "reasoning_content_length": len(reasoning_content),
                "is_public": str(is_public),
                "allowed_users_count": allowed_users_count,
                "segment_number": segment_number,
                "total_segments": total_segments,
                "tags": tags,
                "original_video": original_video
            })
            
            # ctx.logger.info(f"[PARSER] Parsed embedding - filename: {filename}, dims: {embedding_dimensions}, segment: {segment_number}/{total_segments}")

        with ctx.tracer.start_as_current_span("Embedding Validation") as validation_span:
            if not validate_embedding(embedding):
                # ctx.logger.warning("[SKIP] No valid embedding to store")
                validation_span.set_attributes({"valid": False})
                return {"status": "skipped", "reason": "No valid embedding"}
            
            validation_span.set_attributes({"valid": True})

        with ctx.tracer.start_as_current_span("VastDB Storage") as storage_span:
            ctx.logger.info(f"[VASTDB] Storing vector to VastDB for segment {segment_number}/{total_segments}")
            
            success = ctx.vastdb_client.store_vector(embedding_event)
            
            table_full_name = f"{ctx.vastdb_client.bucket}.{ctx.vastdb_client.schema_name}.{ctx.vastdb_client.table_name}"
            
            storage_span.set_attributes({
                "storage_success": success,
                "filename": filename,
                "vector_dimensions": len(embedding),
                "table_name": table_full_name,
                "segment_number": segment_number,
                "total_segments": total_segments,
                "original_video": original_video
            })
            
            if success:
                ctx.logger.info(f"[VASTDB] Successfully stored segment {segment_number}/{total_segments} to {table_full_name}")
            else:
                ctx.logger.error(f"[VASTDB] Failed to store segment {segment_number}/{total_segments}")

        result = {
            "source": source,
            "filename": filename,
            "embedding_dimensions": len(embedding),
            "embedding_model": embedding_model,
            "storage_success": success,
            "status": "success" if success else "error"
        }
        
        ctx.logger.info(f"[SUCCESS] VastDB write completed for segment {segment_number}/{total_segments} of {original_video}")
        return result
        
    except Exception as e:
        ctx.logger.error(f"[ERROR] Handler processing failed: {e}", exc_info=True)
        return {"status": "error", "error": f"Handler processing failed: {e}"}

