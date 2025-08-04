import time
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PerformanceTracker:
    """Enhanced performance tracker with better metrics and logging"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.file_times = {}
        self.phase_times = {}
        self.failed_files = []
        self.successful_files = []
        
    def start_tracking(self, operation_name="Operation"):
        """Start timing an operation"""
        self.start_time = time.time()
        self.operation_name = operation_name
        self.failed_files = []
        self.successful_files = []
        timestamp = datetime.now().strftime('%H:%M:%S')
        message = f"⏱️ Starting {operation_name} at {timestamp}"
        print(message)
        logger.info(message)
        
    def track_phase(self, phase_name):
        """Track time for a specific phase"""
        current_time = time.time()
        if hasattr(self, '_last_phase_time'):
            phase_duration = current_time - self._last_phase_time
            self.phase_times[self._last_phase_name] = phase_duration
            logger.debug(f"Phase '{self._last_phase_name}' completed in {phase_duration:.2f}s")
        self._last_phase_time = current_time
        self._last_phase_name = phase_name
        
    def track_file(self, filename, file_start_time, success=True):
        """Track time for individual file processing"""
        file_duration = time.time() - file_start_time
        self.file_times[filename] = file_duration
        
        if success:
            self.successful_files.append(filename)
            logger.info(f"✅ Successfully processed: {os.path.basename(filename)} ({file_duration:.2f}s)")
        else:
            self.failed_files.append(filename)
            logger.error(f"❌ Failed to process: {os.path.basename(filename)} ({file_duration:.2f}s)")
        
    def end_tracking(self):
        """End timing and calculate total duration"""
        self.end_time = time.time()
        total_duration = self.end_time - self.start_time
        
        # Track final phase
        if hasattr(self, '_last_phase_time'):
            phase_duration = self.end_time - self._last_phase_time
            self.phase_times[self._last_phase_name] = phase_duration
            
        message = f"⏱️ {self.operation_name} completed in {total_duration:.2f} seconds"
        print(message)
        logger.info(message)
        logger.info(f"Success rate: {len(self.successful_files)}/{len(self.successful_files) + len(self.failed_files)} files")
        
        return total_duration
        
    def get_detailed_report(self):
        """Generate detailed performance report"""
        total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        report = f"📊 Performance Report:\n"
        report += f"⏱️ Total Duration: {total_duration:.2f} seconds\n"
        report += f"✅ Successful: {len(self.successful_files)} files\n"
        report += f"❌ Failed: {len(self.failed_files)} files\n"
        
        if self.phase_times:
            report += f"\n🔄 Phase Breakdown:\n"
            for phase, duration in self.phase_times.items():
                percentage = (duration / total_duration * 100) if total_duration > 0 else 0
                report += f"  • {phase}: {duration:.2f}s ({percentage:.1f}%)\n"
        
        if self.file_times:
            report += f"\n📄 File Processing Times:\n"
            sorted_files = sorted(self.file_times.items(), key=lambda x: x[1], reverse=True)
            for filename, duration in sorted_files[:5]:  # Show top 5 slowest files
                report += f"  • {os.path.basename(filename)}: {duration:.2f}s\n"
            
            if len(sorted_files) > 5:
                report += f"  ... and {len(sorted_files) - 5} more files\n"
                
            avg_time = sum(self.file_times.values()) / len(self.file_times)
            report += f"\n📈 Average per file: {avg_time:.2f}s\n"
            report += f"🐌 Slowest file: {max(self.file_times.values()):.2f}s\n"
            report += f"⚡ Fastest file: {min(self.file_times.values()):.2f}s\n"
        
        if self.failed_files:
            report += f"\n❌ Failed Files:\n"
            for failed_file in self.failed_files:
                report += f"  • {os.path.basename(failed_file)}\n"
        
        return report