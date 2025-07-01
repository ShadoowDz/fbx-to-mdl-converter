"""
Logging utility for FBX to MDL Converter
Provides consistent logging across the application
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional
import colorlog

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
import config


def setup_logger(name: str, log_level: str = "INFO") -> logging.Logger:
    """Setup logger with consistent formatting"""
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler with colors
    if config.LOG_TO_CONSOLE:
        console_handler = colorlog.StreamHandler(sys.stdout)
        console_formatter = colorlog.ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if config.LOG_TO_FILE:
        # Ensure log directory exists
        log_dir = os.path.dirname(config.LOG_FILE_PATH)
        if log_dir:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(config.LOG_FILE_PATH, mode='a', encoding='utf-8')
        file_formatter = logging.Formatter(config.LOG_FORMAT, datefmt=config.LOG_DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


class ProgressLogger:
    """Logger with progress tracking capabilities"""
    
    def __init__(self, logger: logging.Logger, total_steps: int, description: str = "Processing"):
        self.logger = logger
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        
    def step(self, message: str = ""):
        """Log a step in the process"""
        self.current_step += 1
        percentage = (self.current_step / self.total_steps) * 100
        
        progress_msg = f"{self.description}: {self.current_step}/{self.total_steps} ({percentage:.1f}%)"
        if message:
            progress_msg += f" - {message}"
        
        self.logger.info(progress_msg)
    
    def finish(self, message: str = "Completed"):
        """Log completion"""
        self.logger.info(f"{self.description}: {message}")


class ConversionLogger:
    """Specialized logger for conversion operations"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.warnings = []
        self.errors = []
        self.stats = {}
    
    def log_conversion_start(self, input_file: str, output_file: str):
        """Log start of conversion"""
        self.logger.info("=" * 60)
        self.logger.info(f"Starting FBX to MDL conversion")
        self.logger.info(f"Input:  {input_file}")
        self.logger.info(f"Output: {output_file}")
        self.logger.info("=" * 60)
    
    def log_conversion_end(self, success: bool):
        """Log end of conversion with summary"""
        self.logger.info("=" * 60)
        if success:
            self.logger.info("Conversion completed successfully!")
        else:
            self.logger.error("Conversion failed!")
        
        self.logger.info(f"Warnings: {len(self.warnings)}")
        self.logger.info(f"Errors: {len(self.errors)}")
        
        # Log statistics
        for key, value in self.stats.items():
            self.logger.info(f"{key}: {value}")
        
        self.logger.info("=" * 60)
    
    def log_phase_start(self, phase: str):
        """Log start of a conversion phase"""
        self.logger.info(f"[{phase.upper()}] Starting...")
    
    def log_phase_end(self, phase: str, success: bool = True):
        """Log end of a conversion phase"""
        status = "Completed" if success else "Failed"
        self.logger.info(f"[{phase.upper()}] {status}")
    
    def log_geometry_stats(self, vertices: int, triangles: int, meshes: int = 1):
        """Log geometry statistics"""
        self.logger.info(f"Geometry: {vertices} vertices, {triangles} triangles, {meshes} meshes")
        self.stats.update({
            "Vertices": vertices,
            "Triangles": triangles,
            "Meshes": meshes
        })
    
    def log_bone_stats(self, bone_count: int, optimized_count: Optional[int] = None):
        """Log bone statistics"""
        if optimized_count is not None:
            self.logger.info(f"Bones: {bone_count} -> {optimized_count} (optimized)")
            self.stats["Bones (optimized)"] = optimized_count
        else:
            self.logger.info(f"Bones: {bone_count}")
        self.stats["Bones"] = bone_count
    
    def log_animation_stats(self, sequence_count: int, frame_count: int):
        """Log animation statistics"""
        self.logger.info(f"Animations: {sequence_count} sequences, {frame_count} total frames")
        self.stats.update({
            "Animation sequences": sequence_count,
            "Animation frames": frame_count
        })
    
    def log_texture_stats(self, texture_count: int, converted_count: int = 0):
        """Log texture statistics"""
        if converted_count > 0:
            self.logger.info(f"Textures: {texture_count} found, {converted_count} converted")
            self.stats["Textures (converted)"] = converted_count
        else:
            self.logger.info(f"Textures: {texture_count}")
        self.stats["Textures"] = texture_count
    
    def log_validation_result(self, result_type: str, passed: bool, details: str = ""):
        """Log validation results"""
        status = "PASSED" if passed else "FAILED"
        message = f"Validation [{result_type}]: {status}"
        if details:
            message += f" - {details}"
        
        if passed:
            self.logger.info(message)
        else:
            self.logger.warning(message)
            self.warnings.append(f"Validation {result_type}: {details}")
    
    def log_cs16_compliance(self, checks: dict):
        """Log CS 1.6 compliance check results"""
        self.logger.info("CS 1.6 Compliance Check:")
        all_passed = True
        
        for check_name, (passed, limit, actual) in checks.items():
            status = "✓" if passed else "✗"
            self.logger.info(f"  {status} {check_name}: {actual}/{limit}")
            if not passed:
                all_passed = False
                self.warnings.append(f"{check_name} limit exceeded: {actual}/{limit}")
        
        if all_passed:
            self.logger.info("All CS 1.6 limits satisfied!")
        else:
            self.logger.warning("Some CS 1.6 limits exceeded!")
    
    def log_optimization_result(self, optimization_type: str, before: int, after: int):
        """Log optimization results"""
        reduction = before - after
        percentage = (reduction / before * 100) if before > 0 else 0
        self.logger.info(f"Optimization [{optimization_type}]: {before} -> {after} (-{reduction}, -{percentage:.1f}%)")
    
    def add_warning(self, message: str):
        """Add a warning message"""
        self.logger.warning(message)
        self.warnings.append(message)
    
    def add_error(self, message: str):
        """Add an error message"""
        self.logger.error(message)
        self.errors.append(message)
    
    def has_errors(self) -> bool:
        """Check if any errors were logged"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if any warnings were logged"""
        return len(self.warnings) > 0


class PerformanceLogger:
    """Logger for performance monitoring"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.timings = {}
        self.start_times = {}
    
    def start_timing(self, operation: str):
        """Start timing an operation"""
        import time
        self.start_times[operation] = time.time()
        if config.BENCHMARK_PERFORMANCE:
            self.logger.debug(f"Starting timing: {operation}")
    
    def end_timing(self, operation: str):
        """End timing an operation"""
        import time
        if operation in self.start_times:
            elapsed = time.time() - self.start_times[operation]
            self.timings[operation] = elapsed
            if config.BENCHMARK_PERFORMANCE:
                self.logger.info(f"Timing [{operation}]: {elapsed:.3f}s")
            del self.start_times[operation]
    
    def log_memory_usage(self, operation: str = "Current"):
        """Log current memory usage"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if config.BENCHMARK_PERFORMANCE:
                self.logger.info(f"Memory usage [{operation}]: {memory_mb:.1f} MB")
                
        except ImportError:
            pass  # psutil not available
    
    def log_performance_summary(self):
        """Log overall performance summary"""
        if not config.BENCHMARK_PERFORMANCE or not self.timings:
            return
        
        self.logger.info("Performance Summary:")
        total_time = sum(self.timings.values())
        
        for operation, time_taken in sorted(self.timings.items(), key=lambda x: x[1], reverse=True):
            percentage = (time_taken / total_time * 100) if total_time > 0 else 0
            self.logger.info(f"  {operation}: {time_taken:.3f}s ({percentage:.1f}%)")
        
        self.logger.info(f"Total processing time: {total_time:.3f}s")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the standard setup"""
    return setup_logger(name, config.LOG_LEVEL)


def create_conversion_logger(name: str) -> ConversionLogger:
    """Create a conversion logger with the standard setup"""
    base_logger = get_logger(name)
    return ConversionLogger(base_logger)


def create_performance_logger(name: str) -> PerformanceLogger:
    """Create a performance logger with the standard setup"""
    base_logger = get_logger(name)
    return PerformanceLogger(base_logger)


# Module-level convenience functions
def log_system_info():
    """Log system information"""
    import platform
    import sys
    
    logger = get_logger(__name__)
    logger.info("System Information:")
    logger.info(f"  Platform: {platform.platform()}")
    logger.info(f"  Python: {sys.version}")
    logger.info(f"  Architecture: {platform.architecture()[0]}")
    
    # Log FBX SDK availability
    try:
        import fbx
        logger.info("  FBX SDK: Available")
    except ImportError:
        logger.warning("  FBX SDK: Not available")


def cleanup_old_logs(days_to_keep: int = 7):
    """Clean up old log files"""
    if not config.LOG_TO_FILE:
        return
    
    import time
    import glob
    
    logger = get_logger(__name__)
    log_dir = os.path.dirname(config.LOG_FILE_PATH)
    
    if not os.path.exists(log_dir):
        return
    
    # Find old log files
    log_pattern = os.path.join(log_dir, "*.log*")
    current_time = time.time()
    cutoff_time = current_time - (days_to_keep * 24 * 60 * 60)
    
    deleted_count = 0
    for log_file in glob.glob(log_pattern):
        if os.path.getmtime(log_file) < cutoff_time:
            try:
                os.remove(log_file)
                deleted_count += 1
            except OSError:
                pass
    
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} old log files")


# Initialize logging on module import
if __name__ != "__main__":
    # Clean up old logs on startup
    cleanup_old_logs()
    
    # Log system info if in debug mode
    if config.DEBUG_MODE:
        log_system_info()