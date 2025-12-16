import logging
import tempfile
import os
import math
import gc
from typing import List, Tuple, Callable, Optional
from moviepy.editor import VideoFileClip


class VideoProcessor:
    """Video processing utilities for segmentation"""
    
    def __init__(self, settings):
        """Initialize video processor with settings"""
        self.settings = settings
        self.segment_duration = settings.segment_duration
        self.output_codec = settings.output_codec
        self.output_format = settings.output_format
    
    def process_video_segments(
        self, 
        video_content: bytes, 
        original_filename: str, 
        upload_callback: Optional[Callable] = None
    ) -> List[Tuple[bytes, int, int, float, float, float]]:
        """
        Process video into segments with optional upload callback per segment
        
        Args:
            video_content: Raw video bytes
            original_filename: Original video filename
            upload_callback: Optional callback to upload segment after creation
        
        Returns:
            List of tuples: (segment_content, segment_number, total_segments, duration, start_time, end_time)
        """
        segments = []
        
        # Create temporary file for input video
        with tempfile.NamedTemporaryFile(suffix=f".{self.output_format}", delete=False) as temp_input:
            temp_input.write(video_content)
            temp_input.flush()
            temp_input_path = temp_input.name
        
        try:
            # Load video with moviepy
            logging.info(f"Loading video file: {original_filename}")
            clip = VideoFileClip(temp_input_path)
            total_duration = clip.duration
            total_segments = math.ceil(total_duration / self.segment_duration)
            
            logging.info(f"Video duration: {total_duration:.2f}s, creating {total_segments} segments of {self.segment_duration}s each")
            
            # Process each segment
            for i in range(total_segments):
                start_time = i * self.segment_duration
                end_time = min((i + 1) * self.segment_duration, total_duration)
                segment_duration = end_time - start_time
                
                logging.info(f"Creating segment {i + 1}/{total_segments}: {start_time:.2f}s - {end_time:.2f}s (duration: {segment_duration:.2f}s)")
                
                # Create segment
                segment_clip = clip.subclip(start_time, end_time)
                
                # Create temporary file for segment
                with tempfile.NamedTemporaryFile(suffix=f".{self.output_format}", delete=False) as temp_output:
                    temp_output_path = temp_output.name
                
                try:
                    # Write segment to file
                    segment_clip.write_videofile(
                        temp_output_path,
                        codec=self.output_codec,
                        audio=False,
                        logger=None
                    )
                    
                    # Close the clip immediately after writing and delete reader
                    segment_clip.close()
                    del segment_clip
                    
                    # Read segment content
                    with open(temp_output_path, 'rb') as f:
                        segment_content = f.read()
                    
                    segment_info = (
                        segment_content, 
                        i + 1,  # segment_number (1-indexed)
                        total_segments, 
                        segment_duration,
                        start_time,
                        end_time
                    )
                    
                    logging.info(f"Created segment {i + 1}/{total_segments}: {len(segment_content)} bytes, duration: {segment_duration:.2f}s")
                    
                    # Upload segment if callback provided
                    if upload_callback:
                        try:
                            upload_callback(segment_info, original_filename)
                            logging.info(f"Uploaded segment {i + 1}/{total_segments}")
                            # Don't accumulate in memory when using callback - free memory immediately
                            del segment_content
                        except Exception as e:
                            logging.error(f"Failed to upload segment {i + 1}/{total_segments}: {e}")
                    else:
                        # Only keep in memory if no callback (batch processing)
                        segments.append(segment_info)
                    
                except Exception as e:
                    # Try to close segment clip if it's still open
                    try:
                        segment_clip.close()
                    except:
                        pass
                    raise e
                finally:
                    # Clean up segment file
                    if os.path.exists(temp_output_path):
                        os.unlink(temp_output_path)
                    # Force garbage collection after each segment to free memory
                    gc.collect()
            
            clip.close()
            del clip
            # Force final garbage collection
            gc.collect()
            
        finally:
            # Clean up input file
            if os.path.exists(temp_input_path):
                os.unlink(temp_input_path)
        
        logging.info(f"Successfully created {len(segments)} video segments")
        return segments
    
    def get_video_info(self, video_content: bytes) -> Tuple[float, int, int]:
        """
        Get video metadata
        
        Returns:
            Tuple of (duration, width, height)
        """
        # Create temporary file for input video
        with tempfile.NamedTemporaryFile(suffix=f".{self.output_format}", delete=False) as temp_input:
            temp_input.write(video_content)
            temp_input.flush()
            temp_input_path = temp_input.name
        
        try:
            clip = VideoFileClip(temp_input_path)
            duration = clip.duration
            width = clip.w
            height = clip.h
            clip.close()
            
            logging.info(f"Video info - Duration: {duration:.2f}s, Resolution: {width}x{height}")
            return duration, width, height
            
        finally:
            # Clean up input file
            if os.path.exists(temp_input_path):
                os.unlink(temp_input_path)

