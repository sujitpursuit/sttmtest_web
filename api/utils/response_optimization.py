"""
Response Optimization Utilities

Provides utilities for optimizing API responses for large reports,
including compression, streaming, pagination, and size management.
"""

import json
import gzip
import io
from typing import Dict, Any, Optional, List, Union
from fastapi import Response
from fastapi.responses import StreamingResponse, JSONResponse
import logging


class ResponseOptimizer:
    """Handles optimization of API responses for large data"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.size_thresholds = {
            'small': 1024 * 10,      # 10KB
            'medium': 1024 * 100,    # 100KB  
            'large': 1024 * 1024,    # 1MB
            'xlarge': 1024 * 1024 * 5 # 5MB
        }
    
    def optimize_response(self, data: Dict[str, Any], 
                         compression: bool = True,
                         pagination: Optional[Dict[str, int]] = None) -> Response:
        """
        Optimize response based on data size and client capabilities
        
        Args:
            data: Response data
            compression: Whether to enable compression
            pagination: Optional pagination parameters
            
        Returns:
            Optimized FastAPI Response
        """
        
        # Convert to JSON string to measure size
        json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        response_size = len(json_str.encode('utf-8'))
        
        self.logger.debug(f"Response size: {response_size} bytes ({response_size/1024:.2f} KB)")
        
        # Apply pagination if data is large and pagination is available
        if pagination and response_size > self.size_thresholds['large']:
            data = self._apply_pagination(data, pagination)
            json_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            response_size = len(json_str.encode('utf-8'))
        
        # Choose optimization strategy based on size
        if response_size <= self.size_thresholds['small']:
            # Small responses - no optimization needed
            return JSONResponse(content=data)
        
        elif response_size <= self.size_thresholds['medium']:
            # Medium responses - light optimization
            return self._create_optimized_json_response(data, compression=compression)
        
        elif response_size <= self.size_thresholds['large']:
            # Large responses - compression + streaming
            if compression:
                return self._create_compressed_response(json_str)
            else:
                return self._create_streaming_response(data)
        
        else:
            # Very large responses - full optimization
            return self._create_streaming_compressed_response(data)
    
    def _create_optimized_json_response(self, data: Dict[str, Any], 
                                      compression: bool = True) -> JSONResponse:
        """Create optimized JSON response with minimal formatting"""
        
        response = JSONResponse(
            content=data,
            headers={
                "Cache-Control": "public, max-age=300",  # 5 minute cache
                "X-Content-Optimized": "true"
            }
        )
        
        if compression:
            response.headers["X-Compression-Available"] = "gzip"
        
        return response
    
    def _create_compressed_response(self, json_str: str) -> Response:
        """Create gzip compressed response"""
        
        # Compress the JSON string
        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode='wb') as gz_file:
            gz_file.write(json_str.encode('utf-8'))
        
        compressed_data = buffer.getvalue()
        compression_ratio = len(compressed_data) / len(json_str.encode('utf-8'))
        
        self.logger.debug(f"Compression ratio: {compression_ratio:.2f} "
                         f"({len(compressed_data)} / {len(json_str.encode('utf-8'))} bytes)")
        
        return Response(
            content=compressed_data,
            media_type="application/json",
            headers={
                "Content-Encoding": "gzip",
                "Content-Length": str(len(compressed_data)),
                "X-Original-Size": str(len(json_str.encode('utf-8'))),
                "X-Compressed-Size": str(len(compressed_data)),
                "X-Compression-Ratio": f"{compression_ratio:.3f}",
                "Cache-Control": "public, max-age=300"
            }
        )
    
    def _create_streaming_response(self, data: Dict[str, Any]) -> StreamingResponse:
        """Create streaming response for large data"""
        
        def generate_json_stream():
            """Generator for streaming JSON data"""
            yield '{'
            
            first_item = True
            for key, value in data.items():
                if not first_item:
                    yield ','
                first_item = False
                
                # Stream key
                yield f'"{key}":'
                
                # Stream value (handle large arrays/objects specially)
                if isinstance(value, (list, dict)) and self._estimate_size(value) > self.size_thresholds['medium']:
                    yield from self._stream_large_value(value)
                else:
                    yield json.dumps(value, ensure_ascii=False, separators=(',', ':'))
            
            yield '}'
        
        return StreamingResponse(
            generate_json_stream(),
            media_type="application/json",
            headers={
                "X-Content-Streamed": "true",
                "Cache-Control": "public, max-age=300"
            }
        )
    
    def _create_streaming_compressed_response(self, data: Dict[str, Any]) -> StreamingResponse:
        """Create streaming + compressed response for very large data"""
        
        def generate_compressed_stream():
            """Generator for streaming compressed JSON data"""
            
            # Create gzip compressor
            compressor = gzip.GzipFile(fileobj=None, mode='wb')
            
            # Start JSON object
            chunk = compressor.compress(b'{')
            if chunk:
                yield chunk
            
            first_item = True
            for key, value in data.items():
                if not first_item:
                    chunk = compressor.compress(b',')
                    if chunk:
                        yield chunk
                first_item = False
                
                # Compress key
                key_json = f'"{key}":'.encode('utf-8')
                chunk = compressor.compress(key_json)
                if chunk:
                    yield chunk
                
                # Compress value
                if isinstance(value, (list, dict)) and self._estimate_size(value) > self.size_thresholds['medium']:
                    # Stream large values in chunks
                    for value_chunk in self._stream_large_value_bytes(value):
                        compressed_chunk = compressor.compress(value_chunk)
                        if compressed_chunk:
                            yield compressed_chunk
                else:
                    value_json = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
                    chunk = compressor.compress(value_json)
                    if chunk:
                        yield chunk
            
            # End JSON object and flush compressor
            chunk = compressor.compress(b'}')
            if chunk:
                yield chunk
            
            # Final flush
            final_chunk = compressor.flush()
            if final_chunk:
                yield final_chunk
        
        return StreamingResponse(
            generate_compressed_stream(),
            media_type="application/json",
            headers={
                "Content-Encoding": "gzip",
                "X-Content-Streamed": "true",
                "X-Content-Compressed": "true",
                "Cache-Control": "public, max-age=300"
            }
        )
    
    def _stream_large_value(self, value: Union[List, Dict]) -> iter:
        """Stream large arrays or objects"""
        
        if isinstance(value, list):
            yield '['
            for i, item in enumerate(value):
                if i > 0:
                    yield ','
                yield json.dumps(item, ensure_ascii=False, separators=(',', ':'))
            yield ']'
        
        elif isinstance(value, dict):
            yield '{'
            first_item = True
            for k, v in value.items():
                if not first_item:
                    yield ','
                first_item = False
                yield f'"{k}":'
                yield json.dumps(v, ensure_ascii=False, separators=(',', ':'))
            yield '}'
    
    def _stream_large_value_bytes(self, value: Union[List, Dict]) -> iter:
        """Stream large values as bytes for compression"""
        
        if isinstance(value, list):
            yield b'['
            for i, item in enumerate(value):
                if i > 0:
                    yield b','
                yield json.dumps(item, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
            yield b']'
        
        elif isinstance(value, dict):
            yield b'{'
            first_item = True
            for k, v in value.items():
                if not first_item:
                    yield b','
                first_item = False
                yield f'"{k}":'.encode('utf-8')
                yield json.dumps(v, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
            yield b'}'
    
    def _apply_pagination(self, data: Dict[str, Any], pagination: Dict[str, int]) -> Dict[str, Any]:
        """Apply pagination to large data structures"""
        
        page = pagination.get('page', 1)
        limit = pagination.get('limit', 100)
        offset = (page - 1) * limit
        
        paginated_data = data.copy()
        
        # Look for large arrays to paginate
        for key, value in data.items():
            if isinstance(value, list) and len(value) > limit:
                total_items = len(value)
                paginated_items = value[offset:offset + limit]
                
                paginated_data[key] = paginated_items
                paginated_data[f"{key}_pagination"] = {
                    "current_page": page,
                    "items_per_page": limit,
                    "total_items": total_items,
                    "total_pages": (total_items + limit - 1) // limit,
                    "has_next": offset + limit < total_items,
                    "has_previous": page > 1
                }
        
        return paginated_data
    
    def _estimate_size(self, obj: Any) -> int:
        """Estimate the serialized size of an object"""
        try:
            return len(json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
        except:
            return 0
    
    def get_size_category(self, size_bytes: int) -> str:
        """Get size category for a given byte size"""
        if size_bytes <= self.size_thresholds['small']:
            return 'small'
        elif size_bytes <= self.size_thresholds['medium']:
            return 'medium'
        elif size_bytes <= self.size_thresholds['large']:
            return 'large'
        else:
            return 'xlarge'


class PaginationHelper:
    """Helper for implementing pagination in large responses"""
    
    @staticmethod
    def paginate_list(items: List[Any], page: int = 1, limit: int = 100) -> Dict[str, Any]:
        """Paginate a list of items"""
        
        total_items = len(items)
        offset = (page - 1) * limit
        
        # Ensure valid page number
        max_page = max(1, (total_items + limit - 1) // limit)
        page = max(1, min(page, max_page))
        offset = (page - 1) * limit
        
        paginated_items = items[offset:offset + limit]
        
        return {
            "items": paginated_items,
            "pagination": {
                "current_page": page,
                "items_per_page": limit,
                "total_items": total_items,
                "total_pages": max_page,
                "has_next": page < max_page,
                "has_previous": page > 1,
                "next_page": page + 1 if page < max_page else None,
                "previous_page": page - 1 if page > 1 else None
            }
        }
    
    @staticmethod
    def create_pagination_links(base_url: str, pagination: Dict[str, Any]) -> Dict[str, str]:
        """Create pagination links for API responses"""
        
        links = {}
        current_page = pagination["current_page"]
        total_pages = pagination["total_pages"]
        
        if pagination["has_previous"]:
            links["previous"] = f"{base_url}?page={current_page - 1}"
            links["first"] = f"{base_url}?page=1"
        
        if pagination["has_next"]:
            links["next"] = f"{base_url}?page={current_page + 1}"
            links["last"] = f"{base_url}?page={total_pages}"
        
        links["self"] = f"{base_url}?page={current_page}"
        
        return links