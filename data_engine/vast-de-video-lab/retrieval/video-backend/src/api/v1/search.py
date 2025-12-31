"""
Semantic video search API endpoints
"""
import logging
from fastapi import APIRouter, HTTPException, status, Depends
from src.schemas.search import VideoSearchRequest, VideoSearchResponse
from src.services.auth_service import CurrentUser
from src.services.embedding_service import get_embedding_service
from src.services.vastdb_service import get_vastdb_service
from src.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=VideoSearchResponse)
async def search_videos(
    request: VideoSearchRequest,
    current_user: CurrentUser
):
    """
    Semantic search for video segments
    
    Performs the following steps:
    1. Generate embedding for search query using NVIDIA NIM
    2. Execute similarity search on VastDB
    3. Filter results by user permissions
    4. Return top-k results with similarity scores
    
    Args:
        request: Search request with query, top_k, filters
        current_user: Current authenticated user
        
    Returns:
        Search results with metadata and timings
    """
    logger.info(f"Search request from {current_user.username}: query='{request.query}', top_k={request.top_k}, use_llm={request.use_llm}, min_similarity={request.min_similarity}, llm_top_n={request.llm_top_n}")
    
    try:
        # Step 1: Generate embedding for query
        embedding_service = get_embedding_service()
        logger.info(f"[EMBEDDING] Generating embedding for query: '{request.query}'")
        
        query_embedding, embedding_time_ms = embedding_service.generate_embedding(request.query, input_type="query")
        logger.info(f"Generated embedding in {embedding_time_ms:.2f}ms")
        
        # Perform similarity search
        vastdb_service = get_vastdb_service()
        logger.info(f"[SEARCH] Performing similarity search on VastDB (include_public={request.include_public})")
        
        results, search_time_ms, permission_filtered, formatted_sql = vastdb_service.similarity_search(
            query_embedding=query_embedding,
            top_k=request.top_k,
            user=current_user,
            tags=request.tags if request.tags else None,
            include_public=request.include_public,
            time_filter=request.time_filter,
            custom_start_date=request.custom_start_date,
            custom_end_date=request.custom_end_date,
            metadata_filters=request.metadata_filters,
            min_similarity=request.min_similarity,
            user_query_text=request.query
        )
        
        logger.info(f"[SEARCH] Found {len(results)} results in {search_time_ms:.2f}ms")
        logger.info(f"[SEARCH] Permission filtered: {permission_filtered} videos")
        
        # Log top result scores for debugging
        if results:
            top_scores = [f"{r.similarity_score:.4f}" for r in results[:3]]
            logger.debug(f"[SEARCH] Top scores: {', '.join(top_scores)}")
        
        # Step 4: Generate LLM synthesis if requested
        llm_synthesis = None
        if request.use_llm and len(results) > 0:
            # Limit results sent to LLM using llm_top_n setting
            llm_results = results[:request.llm_top_n]
            logger.info(f"[LLM] Generating AI synthesis for top {len(llm_results)} results (llm_top_n={request.llm_top_n})")
            try:
                llm_service = get_llm_service()
                # Convert results to dict format for LLM service
                results_dict = [
                    {
                        "summary": r.reasoning_content,
                        "source": r.source,
                        "filename": r.filename,
                        "original_video": r.original_video,
                        "segment_number": r.segment_number,
                        "similarity_score": r.similarity_score
                    }
                    for r in llm_results
                ]
                llm_synthesis = llm_service.synthesize_search_results(
                    query=request.query,
                    top_results=results_dict,
                    custom_system_prompt=request.system_prompt  # Custom prompt from GUI
                )
                if request.system_prompt:
                    logger.info(f"[LLM] Using custom system prompt from GUI ({len(request.system_prompt)} chars)")
                logger.info(f"[LLM] Generated synthesis: {llm_synthesis['tokens_used']} tokens, "
                           f"{llm_synthesis['processing_time']}s, used {llm_synthesis['segments_used']} segments")
            except Exception as e:
                logger.error(f"[LLM] Failed to generate synthesis: {e}")
                llm_synthesis = {
                    "response": f"Failed to generate AI synthesis: {str(e)}",
                    "segments_used": 0,
                    "model": "",
                    "tokens_used": 0,
                    "processing_time": 0.0,
                    "error": str(e)
                }
        
        return VideoSearchResponse(
            results=results,
            total=len(results),
            query=request.query,
            embedding_time_ms=embedding_time_ms,
            search_time_ms=search_time_ms,
            permission_filtered=permission_filtered,
            llm_synthesis=llm_synthesis,
            sql_query=formatted_sql
        )
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

