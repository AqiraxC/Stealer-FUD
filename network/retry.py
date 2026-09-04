import os
import sys
import json
import time
import random
import threading
import functools
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Callable

class RetryManager:
    def __init__(self, config=None):
        self.config = config or {}
        self.max_retries = self.config.get("max_retries", 5)
        self.base_delay = self.config.get("retry_delay", 10)
        self.max_delay = self.config.get("max_retry_delay", 300)
        self.backoff_factor = self.config.get("backoff_factor", 2)
        self.jitter_percent = self.config.get("jitter_percent", 20)
        self.retry_history = []
        self.retry_lock = threading.Lock()
        
    def calculate_delay(self, attempt, base_delay=None):
        if base_delay is None:
            base_delay = self.base_delay
        
        # Exponential backoff
        delay = base_delay * (self.backoff_factor ** attempt)
        
        # Cap at max delay
        delay = min(delay, self.max_delay)
        
        # Add jitter
        jitter = delay * (self.jitter_percent / 100)
        delay += random.uniform(-jitter, jitter)
        
        # Ensure minimum delay
        delay = max(0.1, delay)
        
        return delay
    
    def retry_with_backoff(self, func, *args, **kwargs):
        retry_count = kwargs.pop('_retry_count', self.max_retries)
        base_delay = kwargs.pop('_base_delay', self.base_delay)
        
        for attempt in range(retry_count):
            try:
                result = func(*args, **kwargs)
                
                if result:
                    self.log_retry_success(func.__name__, attempt + 1)
                    return result
            except Exception as e:
                self.log_retry_error(func.__name__, attempt + 1, str(e))
            
            if attempt < retry_count - 1:
                delay = self.calculate_delay(attempt, base_delay)
                self.log_retry_wait(func.__name__, attempt + 1, delay)
                time.sleep(delay)
        
        self.log_retry_failure(func.__name__, retry_count)
        return None
    
    def retry_with_linear_backoff(self, func, *args, **kwargs):
        retry_count = kwargs.pop('_retry_count', self.max_retries)
        base_delay = kwargs.pop('_base_delay', self.base_delay)
        
        for attempt in range(retry_count):
            try:
                result = func(*args, **kwargs)
                
                if result:
                    self.log_retry_success(func.__name__, attempt + 1)
                    return result
            except Exception as e:
                self.log_retry_error(func.__name__, attempt + 1, str(e))
            
            if attempt < retry_count - 1:
                delay = base_delay * (attempt + 1)
                delay = min(delay, self.max_delay)
                self.log_retry_wait(func.__name__, attempt + 1, delay)
                time.sleep(delay)
        
        self.log_retry_failure(func.__name__, retry_count)
        return None
    
    def retry_with_fixed_delay(self, func, *args, **kwargs):
        retry_count = kwargs.pop('_retry_count', self.max_retries)
        base_delay = kwargs.pop('_base_delay', self.base_delay)
        
        for attempt in range(retry_count):
            try:
                result = func(*args, **kwargs)
                
                if result:
                    self.log_retry_success(func.__name__, attempt + 1)
                    return result
            except Exception as e:
                self.log_retry_error(func.__name__, attempt + 1, str(e))
            
            if attempt < retry_count - 1:
                self.log_retry_wait(func.__name__, attempt + 1, base_delay)
                time.sleep(base_delay)
        
        self.log_retry_failure(func.__name__, retry_count)
        return None
    
    def retry_with_jitter_only(self, func, *args, **kwargs):
        retry_count = kwargs.pop('_retry_count', self.max_retries)
        base_delay = kwargs.pop('_base_delay', self.base_delay)
        
        for attempt in range(retry_count):
            try:
                result = func(*args, **kwargs)
                
                if result:
                    self.log_retry_success(func.__name__, attempt + 1)
                    return result
            except Exception as e:
                self.log_retry_error(func.__name__, attempt + 1, str(e))
            
            if attempt < retry_count - 1:
                delay = base_delay * random.uniform(0.5, 1.5)
                self.log_retry_wait(func.__name__, attempt + 1, delay)
                time.sleep(delay)
        
        self.log_retry_failure(func.__name__, retry_count)
        return None
    
    def retry_with_timeout(self, func, timeout_seconds=30, *args, **kwargs):
        result_container = []
        exception_container = []
        
        def wrapper():
            try:
                result = func(*args, **kwargs)
                result_container.append(result)
            except Exception as e:
                exception_container.append(e)
        
        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()
        thread.join(timeout=timeout_seconds)
        
        if thread.is_alive():
            self.log_retry_timeout(func.__name__, timeout_seconds)
            return None
        
        if result_container:
            return result_container[0]
        elif exception_container:
            self.log_retry_error(func.__name__, 1, str(exception_container[0]))
            return None
        
        return None
    
    def retry_async(self, func, callback=None, *args, **kwargs):
        def async_wrapper():
            result = self.retry_with_backoff(func, *args, **kwargs)
            
            if callback:
                callback(result)
        
        thread = threading.Thread(target=async_wrapper, daemon=True)
        thread.start()
        
        return thread
    
    def retry_with_circuit_breaker(self, func, failure_threshold=3, reset_timeout=60, *args, **kwargs):
        circuit_open = False
        circuit_opened_at = None
        failure_count = 0
        
        def wrapped_func(*args, **kwargs):
            nonlocal circuit_open, circuit_opened_at, failure_count
            
            if circuit_open:
                if circuit_opened_at and (time.time() - circuit_opened_at) >= reset_timeout:
                    circuit_open = False
                    failure_count = 0
                else:
                    return None
            
            try:
                result = func(*args, **kwargs)
                
                if result:
                    failure_count = 0
                    return result
                else:
                    failure_count += 1
            except:
                failure_count += 1
            
            if failure_count >= failure_threshold:
                circuit_open = True
                circuit_opened_at = time.time()
                self.log_circuit_opened(func.__name__, failure_threshold, reset_timeout)
            
            return None
        
        return wrapped_func
    
    def retry_with_rate_limiting(self, func, rate_limit_seconds=1, *args, **kwargs):
        last_call_time = {}
        
        def wrapped_func(*args, **kwargs):
            func_name = func.__name__
            current_time = time.time()
            
            if func_name in last_call_time:
                elapsed = current_time - last_call_time[func_name]
                
                if elapsed < rate_limit_seconds:
                    wait_time = rate_limit_seconds - elapsed
                    time.sleep(wait_time)
            
            last_call_time[func_name] = time.time()
            
            return self.retry_with_backoff(func, *args, **kwargs)
        
        return wrapped_func
    
    def log_retry_success(self, func_name, attempt):
        with self.retry_lock:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "function": func_name,
                "status": "success",
                "attempt": attempt
            }
            self.retry_history.append(entry)
    
    def log_retry_error(self, func_name, attempt, error):
        with self.retry_lock:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "function": func_name,
                "status": "error",
                "attempt": attempt,
                "error": error
            }
            self.retry_history.append(entry)
    
    def log_retry_wait(self, func_name, attempt, delay):
        with self.retry_lock:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "function": func_name,
                "status": "waiting",
                "attempt": attempt,
                "delay": delay
            }
            self.retry_history.append(entry)
    
    def log_retry_failure(self, func_name, attempts):
        with self.retry_lock:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "function": func_name,
                "status": "failed",
                "attempts": attempts
            }
            self.retry_history.append(entry)
    
    def log_retry_timeout(self, func_name, timeout):
        with self.retry_lock:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "function": func_name,
                "status": "timeout",
                "timeout": timeout
            }
            self.retry_history.append(entry)
    
    def log_circuit_opened(self, func_name, threshold, reset_timeout):
        with self.retry_lock:
            entry = {
                "timestamp": datetime.now().isoformat(),
                "function": func_name,
                "status": "circuit_opened",
                "threshold": threshold,
                "reset_timeout": reset_timeout
            }
            self.retry_history.append(entry)
    
    def get_retry_history(self):
        with self.retry_lock:
            return self.retry_history
    
    def clear_history(self):
        with self.retry_lock:
            self.retry_history = []
    
    def get_statistics(self):
        stats = {
            "total_attempts": 0,
            "successes": 0,
            "failures": 0,
            "timeouts": 0,
            "circuit_opens": 0,
            "average_attempts_per_function": {}
        }
        
        function_attempts = {}
        
        for entry in self.retry_history:
            func_name = entry.get("function", "unknown")
            
            if func_name not in function_attempts:
                function_attempts[func_name] = {
                    "attempts": 0,
                    "successes": 0,
                    "failures": 0
                }
            
            function_attempts[func_name]["attempts"] += 1
            stats["total_attempts"] += 1
            
            if entry.get("status") == "success":
                stats["successes"] += 1
                function_attempts[func_name]["successes"] += 1
            elif entry.get("status") == "failed":
                stats["failures"] += 1
                function_attempts[func_name]["failures"] += 1
            elif entry.get("status") == "timeout":
                stats["timeouts"] += 1
            elif entry.get("status") == "circuit_opened":
                stats["circuit_opens"] += 1
        
        for func_name, attempts in function_attempts.items():
            stats["average_attempts_per_function"][func_name] = attempts["attempts"]
        
        return stats

if __name__ == "__main__":
    retry_manager = RetryManager()
    
    # Example function that fails
    def test_function():
        if random.random() < 0.7:
            raise Exception("Random failure")
        return "Success"
    
    # Retry with backoff
    result = retry_manager.retry_with_backoff(test_function)
    print(f"Result: {result}")
    
    # Get statistics
    stats = retry_manager.get_statistics()
    print(f"Statistics: {json.dumps(stats, indent=2)}")