# 📁 Project Structure Guide

This document explains the modular architecture of the Enhanced PDF B&W Compressor and how each component works together.

## 🏗️ Architecture Overview

The application follows a modular design pattern with clear separation of concerns:

```
┌─────────────────┐
│     main.py     │  ← Entry point, determines GUI/CLI mode
└─────────────────┘
         │
    ┌────┴────┐
    │ GUI     │ CLI   ← User interfaces
    └────┬────┴─────┘
         │
┌─────────────────┐
│ batch_processor │  ← Handles single files and directories
└─────────────────┘
         │
┌─────────────────┐
│ pdf_compressor  │  ← Core Ghostscript integration
└─────────────────┘
         │
    ┌────┴────┐
    │ Utils   │ Perf  ← Support modules
    └─────────┴─────┘
```

## 📄 File Descriptions

### Core Files

#### `main.py` - Application Entry Point
- **Purpose**: Main entry point that determines whether to run GUI or CLI mode
- **Dependencies**: `config`, `gui_interface`, `cli_interface`
- **Key Functions**:
  - `main()`: Determines execution mode based on command line arguments
- **Usage**: `python main.py [args]`

#### `config.py` - Configuration Management
- **Purpose**: Central configuration for all application settings
- **Dependencies**: Built-in Python modules only
- **Key Components**:
  - `QUALITY_SETTINGS`: Compression quality presets
  - `TIMEOUT_SETTINGS`: File size-based timeout calculations
  - `GUI_SETTINGS`: GUI appearance and behavior
  - `setup_logging()`: Logging configuration function
- **Usage**: Imported by other modules for settings

### Core Processing Modules

#### `pdf_compressor.py` - Core Compression Engine
- **Purpose**: Handles the actual PDF compression using Ghostscript
- **Dependencies**: `file_utils`, subprocess, logging
- **Key Functions**:
  - `compress_single_pdf()`: Main compression function with progress tracking
  - `check_ghostscript()`: Validates Ghostscript installation
- **Features**:
  - Adaptive timeout based on file size
  - Real-time progress monitoring
  - Comprehensive error handling
  - Temporary file safety

#### `batch_processor.py` - Batch Operations Manager
- **Purpose**: Handles single files and directory batch processing
- **Dependencies**: `pdf_compressor`, `file_utils`
- **Key Functions**:
  - `compress_directory()`: Process all PDFs in a directory
  - `compress_single_file_wrapper()`: Unified single file interface
- **Features**:
  - Progress callbacks for UI updates
  - Statistics collection
  - Failed file tracking

### User Interfaces

#### `gui_interface.py` - Graphical User Interface
- **Purpose**: Tkinter-based GUI for user-friendly operation
- **Dependencies**: `batch_processor`, `pdf_compressor`, `performance_tracker`
- **Key Components**:
  - `PDFCompressorGUI`: Main GUI class
  - File/directory selection dialogs
  - Real-time progress display
  - Results visualization
- **Features**:
  - Threaded processing to keep UI responsive
  - Progress callbacks and updates
  - Log file viewer integration

#### `cli_interface.py` - Command Line Interface
- **Purpose**: Command-line interface for scripting and automation
- **Dependencies**: `batch_processor`, `pdf_compressor`, `performance_tracker`
- **Key Components**:
  - `PDFCompressorCLI`: Main CLI class
  - Argument parsing and validation
  - Help system
- **Features**:
  - Progress indicators for long operations
  - Comprehensive help text
  - Return codes for scripting

### Utility Modules

#### `file_utils.py` - File Operation Utilities
- **Purpose**: Common file operations and utilities
- **Dependencies**: Built-in Python modules only
- **Key Functions**:
  - `get_file_size()`: Get file size in MB
  - `calculate_timeout()`: Determine processing timeout
  - `safe_remove_file()`: Robust file deletion with retry
  - `create_temp_file()`: Secure temporary file creation
- **Features**:
  - Cross-platform compatibility
  - Retry mechanisms for file operations
  - Logging for all operations

#### `performance_tracker.py` - Performance Monitoring
- **Purpose**: Detailed performance tracking and reporting
- **Dependencies**: Built-in Python modules only
- **Key Components**:
  - `PerformanceTracker`: Main tracking class
  - Phase timing (initialization, processing, cleanup)
  - File-level timing and success tracking
- **Features**:
  - Detailed performance reports
  - Success/failure statistics
  - Time breakdown by phases

### Package Files

#### `__init__.py` - Package Initialization
- **Purpose**: Defines the package structure and exports
- **Contents**:
  - Version information
  - Public API exports
  - Package metadata

## 🔄 Data Flow

### Single File Processing
```
User Input → GUI/CLI → batch_processor → pdf_compressor → Ghostscript
     ↓           ↓            ↓              ↓              ↓
Progress ← UI Update ← Progress CB ← Monitor ← Process Status
     ↓
  Results Display
```

### Directory Processing
```
Directory → File Discovery → Sort by Size → Process Each File
    ↓            ↓              ↓              ↓
Statistics ← Progress Track ← File Results ← Individual Process
    ↓
Final Report
```

## 🔧 Module Interactions

### Import Dependencies
```
main.py
├── config
├── gui_interface
│   ├── batch_processor
│   │   ├── pdf_compressor
│   │   │   └── file_utils
│   │   └── file_utils
│   └── performance_tracker
└── cli_interface
    ├── batch_processor (same as above)
    └── performance_tracker
```

### Key Interfaces

#### Progress Callbacks
```python
def progress_callback(message: str) -> None:
    """Update progress display with current status message"""
```

#### Results Structure
```python
results = {
    'total_files': int,
    'successful_compressions': int, 
    'failed_files': List[Tuple[str, str]],
    'total_original_size': int,
    'total_compressed_size': int,
    'output_dir': str  # for directories
}
```

## 🚀 Extension Points

### Adding New Quality Modes
1. Add preset to `config.py` → `QUALITY_SETTINGS`
2. Update GUI radiobuttons in `gui_interface.py`
3. Update CLI help in `cli_interface.py`

### Adding New Output Formats
1. Modify Ghostscript command in `pdf_compressor.py`
2. Update file extension handling in `batch_processor.py`
3. Update UI labels and descriptions

### Adding New Progress Indicators
1. Implement callback interface in processing modules
2. Update UI components to handle new callback types
3. Add configuration options if needed

## 🧪 Testing Strategy

### Unit Tests
- `test_file_utils.py`: File operation functions
- `test_pdf_compressor.py`: Core compression logic
- `test_performance_tracker.py`: Tracking functionality

### Integration Tests
- `test_batch_processor.py`: End-to-end batch processing
- `test_interfaces.py`: GUI and CLI functionality

### Test Structure
```
tests/
├── unit/
│   ├── test_file_utils.py
│   ├── test_pdf_compressor.py
│   └── test_performance_tracker.py
├── integration/
│   ├── test_batch_processor.py
│   └── test_interfaces.py
├── fixtures/
│   ├── sample.pdf
│   └── test_data/
└── conftest.py
```

This modular structure makes the application:
- **Maintainable**: Each module has a single responsibility
- **Testable**: Clear interfaces allow for comprehensive testing
- **Extensible**: New features can be added without affecting existing code
- **Reusable**: Modules can be used independently or in other projects