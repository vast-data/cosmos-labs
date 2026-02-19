from opentelemetry import trace
from vast_runtime.vast_event import VastEvent  # type: ignore

from common.models import Settings, EmbeddingEvent
from common.vastdb_client import VastDBClient
from common.handler_utils import parse_embedding_event, validate_embedding


def init(ctx):
    """Initialize the serverless function"""
    with ctx.tracer.start_as_current_span("VastDB Writer Initialization"):
        settings = Settings.from_ctx_secrets(ctx.secrets)
        ctx.vastdb_client = VastDBClient(settings)


def handler(ctx, event: VastEvent):
    """Main handler function for vast serverless runtime"""
    
    with ctx.tracer.start_as_current_span("VastDB Writer Handler") as handler_span:
        try:
            data = event.get_data()
            event_type = getattr(event, 'get_type', lambda: 'element_trigger')()
            handler_span.set_attribute("event_type", event_type)
            
            with ctx.tracer.start_as_current_span("Embedding Event Parsing") as parse_span:
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
                
                camera_id = embedding_event.get("camera_id", "")
                capture_type = embedding_event.get("capture_type", "")
                neighborhood = embedding_event.get("neighborhood", "")
                
                allowed_users_count = len(allowed_users.split(",")) if allowed_users else 0
                
                ctx.logger.info(f"[INPUT] {filename} | segment {segment_number}/{total_segments} | {len(embedding)} dims | reasoning={len(reasoning_content)} chars")
                
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
                    "original_video": original_video,
                    "camera_id": camera_id,
                    "capture_type": capture_type,
                    "neighborhood": neighborhood
                })

            with ctx.tracer.start_as_current_span("Embedding Validation") as validation_span:
                if not validate_embedding(embedding):
                    validation_span.set_attributes({"valid": False})
                    ctx.logger.info(f"[SKIP] {filename} | no valid embedding (dims={len(embedding) if embedding else 0})")
                    return {"status": "skipped", "reason": "No valid embedding"}
                
                validation_span.set_attributes({"valid": True})

            with ctx.tracer.start_as_current_span("VastDB Storage") as storage_span:
                table_full_name = f"{ctx.vastdb_client.bucket}.{ctx.vastdb_client.schema_name}.{ctx.vastdb_client.table_name}"
                ctx.logger.info(f"[VASTDB] Writing to {table_full_name}")
                
                success = ctx.vastdb_client.store_vector(embedding_event)
                
                storage_span.set_attributes({
                    "storage_success": success,
                    "filename": filename,
                    "vector_dimensions": len(embedding),
                    "table_name": table_full_name,
                    "segment_number": segment_number,
                    "total_segments": total_segments
                })
                
                if not success:
                    ctx.logger.error(f"[VASTDB] FAILED to store {filename} segment {segment_number}/{total_segments} | table={table_full_name}")

            result = {
                "source": source,
                "filename": filename,
                "embedding_dimensions": len(embedding),
                "embedding_model": embedding_model,
                "storage_success": success,
                "status": "success" if success else "error"
            }
            
            ctx.logger.info(f"[COMPLETE] {filename} | segment {segment_number}/{total_segments} → {table_full_name} | public={is_public} | camera={camera_id or 'none'}")
            return result
            
        except Exception as e:
            handler_span.set_attribute("error", True)
            handler_span.set_attribute("error.message", str(e))
            handler_span.record_exception(e)
            ctx.logger.error(f"VastDB write failed: {e}")
            return {"status": "error", "error": str(e)}

