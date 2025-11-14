from opentelemetry import trace
from vast_runtime.vast_event import VastEvent  # type: ignore
from datetime import datetime, timedelta
import logging

from common.models import Settings
from common.embedding_client import EmbeddingClient
from common.vastdb_client import VastDBClient
from common.twilio_client import TwilioClient


def init(ctx):
    """Initialize the safety alerts function"""
    
    with ctx.tracer.start_as_current_span("Safety Alerts Initialization"):
        settings = Settings.from_ctx_secrets(ctx.secrets)
        
        ctx.embedding_client = EmbeddingClient(settings)
        ctx.vastdb_client = VastDBClient(settings)
        ctx.twilio_client = TwilioClient(settings)
        ctx.settings = settings
        
        ctx.logger.info(f"[INIT] Safety alerts initialized")
        ctx.logger.info(f"[INIT] VastDB: {settings.vdbbucket}.{settings.vdbschema}.{settings.vdbcollection}")
        ctx.logger.info(f"[INIT] Alert queries: {len(settings.alert_queries)}")
        ctx.logger.info(f"[INIT] Cooldown period: {settings.cooldown_minutes} minutes")
        ctx.logger.info(f"[INIT] Lookback window: {settings.alert_lookback_minutes} minutes")


def handler(ctx, event: VastEvent):
    """Main handler for scheduled safety alert detection"""
    
    try:
        event_type = type(event).__name__
        ctx.logger.info(f"[HANDLER] Safety alerts handler started - event type: {event_type}")
        
        with ctx.tracer.start_as_current_span("Safety Alert Detection") as detection_span:
            
            alert_results = []
            
            for query_config in ctx.settings.alert_queries:
                query_text = query_config["query"]
                threshold = query_config.get("threshold", ctx.settings.default_threshold)
                
                ctx.logger.info(f"[QUERY] Processing alert query: '{query_text}' (threshold: {threshold})")
                
                with ctx.tracer.start_as_current_span(f"Alert Query: {query_text}") as query_span:
                    
                    with ctx.tracer.start_as_current_span("Generate Query Embedding"):
                        ctx.logger.info(f"[EMBEDDING] Generating embedding for query: '{query_text}'")
                        embeddings = ctx.embedding_client.get_embeddings([query_text], input_type="query")
                        query_embedding = embeddings[0]
                        ctx.logger.info(f"[EMBEDDING] Generated embedding (dimensions: {len(query_embedding)})")
                    
                    with ctx.tracer.start_as_current_span("Similarity Search"):
                        ctx.logger.info(f"[SEARCH] Performing similarity search (top_k: {ctx.settings.alert_top_k})")
                        results = ctx.vastdb_client.similarity_search(
                            query_embedding=query_embedding,
                            top_k=ctx.settings.alert_top_k,
                            threshold=threshold
                        )
                        ctx.logger.info(f"[SEARCH] Found {len(results)} results above threshold {threshold}")
                    
                    with ctx.tracer.start_as_current_span("Cooldown Filtering"):
                        recent_results = filter_recent_results(ctx, results, query_text)
                        ctx.logger.info(f"[COOLDOWN] {len(recent_results)} new results after cooldown filtering")
                    
                    if recent_results:
                        with ctx.tracer.start_as_current_span("Alert Processing"):
                            for result in recent_results:
                                alert_sent = process_alert(ctx, query_text, result, threshold)
                                if alert_sent:
                                    alert_results.append({
                                        "query": query_text,
                                        "source": result["source"],
                                        "similarity_score": result["similarity_score"],
                                        "timestamp": datetime.utcnow().isoformat()
                                    })
                    else:
                        ctx.logger.info(f"[SKIP] No new alerts for query: '{query_text}'")
                    
                    query_span.set_attributes({
                        "query": query_text,
                        "threshold": threshold,
                        "results_found": len(results),
                        "alerts_sent": len(recent_results)
                    })
            
            detection_span.set_attributes({
                "total_queries": len(ctx.settings.alert_queries),
                "total_alerts_sent": len(alert_results)
            })
            
            ctx.logger.info(f"[SUCCESS] Safety alerts completed - {len(alert_results)} alerts sent")
            
            return {
                "status": "success",
                "alerts_sent": len(alert_results),
                "queries_processed": len(ctx.settings.alert_queries),
                "alerts": alert_results
            }
        
    except Exception as e:
        ctx.logger.error(f"[ERROR] Handler processing failed: {e}", exc_info=True)
        return {"status": "error", "error": f"Handler processing failed: {e}"}


def filter_recent_results(ctx, results, query_text):
    """Filter out results that have already triggered an alert within the cooldown period"""
    
    cooldown_delta = timedelta(minutes=ctx.settings.cooldown_minutes)
    cutoff_time = datetime.utcnow() - cooldown_delta
    
    recent_results = []
    
    for result in results:
        source = result["source"]
        
        last_alert_time = ctx.vastdb_client.get_last_alert_time(query_text, source)
        
        if last_alert_time is None:
            recent_results.append(result)
        elif last_alert_time < cutoff_time:
            ctx.logger.info(f"[COOLDOWN] Alert for '{query_text}' on {source} is outside cooldown period")
            recent_results.append(result)
        else:
            time_remaining = (last_alert_time + cooldown_delta) - datetime.utcnow()
            ctx.logger.info(f"[COOLDOWN] Alert for '{query_text}' on {source} still in cooldown ({time_remaining.seconds}s remaining)")
    
    return recent_results


def process_alert(ctx, query_text, result, threshold):
    """Send SMS alert and store alert record in VastDB"""
    
    try:
        source = result["source"]
        similarity_score = result["similarity_score"]
        reasoning = result["reasoning_content"]
        segment_number = result.get("segment_number", 0)
        original_video = result.get("original_video", "unknown")
        
        ctx.logger.info(f"[ALERT] Processing alert for query: '{query_text}' - score: {similarity_score:.3f}")
        
        with ctx.tracer.start_as_current_span("Send SMS"):
            sms_message = format_alert_message(query_text, similarity_score, original_video, segment_number, reasoning)
            
            sms_sent = ctx.twilio_client.send_sms(sms_message)
            
            if sms_sent:
                ctx.logger.info(f"[SMS] Alert SMS sent successfully")
            else:
                ctx.logger.error(f"[SMS] Failed to send alert SMS")
        
        with ctx.tracer.start_as_current_span("Store Alert Record"):
            alert_record = {
                "alert_query": query_text,
                "source": source,
                "similarity_score": similarity_score,
                "threshold": threshold,
                "reasoning_content": reasoning,
                "original_video": original_video,
                "segment_number": segment_number,
                "sms_sent": sms_sent,
                "timestamp": datetime.utcnow()
            }
            
            stored = ctx.vastdb_client.store_alert(alert_record)
            
            if stored:
                ctx.logger.info(f"[VASTDB] Alert record stored successfully")
            else:
                ctx.logger.error(f"[VASTDB] Failed to store alert record")
        
        return sms_sent and stored
        
    except Exception as e:
        ctx.logger.error(f"[ERROR] Failed to process alert: {e}", exc_info=True)
        return False


def format_alert_message(query_text, score, video_name, segment_num, reasoning):
    """Format SMS alert message"""
    
    message = (
        f"ALERT: {query_text}\n"
        f"Match: {score:.1%}\n"
        f"Video: {video_name} (segment {segment_num})\n"
        f"Details: {reasoning[:100]}..."
    )
    
    return message

