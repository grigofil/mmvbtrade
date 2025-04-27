import os
import re
import datetime
from flask import Blueprint, render_template, jsonify, request, send_file, abort
from config import config
from app.utils.logger import Logger

# Create logger
logger = Logger(name="logs_route")

# Create blueprint
logs_bp = Blueprint('logs', __name__)

@logs_bp.route('/logs')
def logs_page():
    """Render the logs page"""
    log_files = get_log_files()
    return render_template('logs.html', log_files=log_files)

@logs_bp.route('/api/logs/<filename>')
def get_log_content(filename):
    """Get log file content with filtering options"""
    # Validate filename to prevent directory traversal
    if not is_valid_log_file(filename):
        logger.warning(f"Invalid log file requested: {filename}")
        return jsonify({"success": False, "message": "Invalid log file"}), 400
    
    # Get filter parameters
    level = request.args.get('level', 'all')
    search = request.args.get('search', '')
    date_range = request.args.get('date_range', 'all')
    
    try:
        # Get log file path
        log_path = os.path.join(config.LOGS_DIR, filename)
        
        # Check if file exists
        if not os.path.exists(log_path):
            return jsonify({"success": False, "message": "Log file not found"}), 404
        
        # Read file content with filters
        content, line_count = read_log_file(log_path, level, search, date_range)
        
        return jsonify({
            "success": True,
            "filename": filename,
            "content": content,
            "lines": line_count
        })
    
    except Exception as e:
        logger.error(f"Error reading log file {filename}: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@logs_bp.route('/api/logs/<filename>/download')
def download_log(filename):
    """Download log file"""
    # Validate filename to prevent directory traversal
    if not is_valid_log_file(filename):
        logger.warning(f"Invalid log file download requested: {filename}")
        return jsonify({"success": False, "message": "Invalid log file"}), 400
    
    try:
        # Get log file path
        log_path = os.path.join(config.LOGS_DIR, filename)
        
        # Check if file exists
        if not os.path.exists(log_path):
            return jsonify({"success": False, "message": "Log file not found"}), 404
        
        # Send file for download
        return send_file(log_path, as_attachment=True, download_name=filename)
    
    except Exception as e:
        logger.error(f"Error downloading log file {filename}: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@logs_bp.route('/api/logs/<filename>/clear', methods=['POST'])
def clear_log(filename):
    """Clear log file content"""
    # Validate filename to prevent directory traversal
    if not is_valid_log_file(filename):
        logger.warning(f"Invalid log file clear requested: {filename}")
        return jsonify({"success": False, "message": "Invalid log file"}), 400
    
    try:
        # Get log file path
        log_path = os.path.join(config.LOGS_DIR, filename)
        
        # Check if file exists
        if not os.path.exists(log_path):
            return jsonify({"success": False, "message": "Log file not found"}), 404
        
        # Clear file content
        with open(log_path, 'w') as f:
            f.write(f"Log file cleared at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        logger.info(f"Log file {filename} cleared")
        return jsonify({"success": True, "message": "Log file cleared"})
    
    except Exception as e:
        logger.error(f"Error clearing log file {filename}: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

def get_log_files():
    """Get list of log files with metadata"""
    log_files = []
    
    try:
        # Check if logs directory exists
        if not os.path.exists(config.LOGS_DIR):
            logger.warning(f"Logs directory not found: {config.LOGS_DIR}")
            return log_files
        
        # Get files in logs directory
        files = [f for f in os.listdir(config.LOGS_DIR) if os.path.isfile(os.path.join(config.LOGS_DIR, f))]
        
        # Filter log files
        log_files_raw = [f for f in files if f.endswith('.log')]
        
        # Add metadata for each file
        for filename in log_files_raw:
            file_path = os.path.join(config.LOGS_DIR, filename)
            
            # Get file stats
            stats = os.stat(file_path)
            
            # Format size
            size_bytes = stats.st_size
            if size_bytes < 1024:
                size = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size = f"{size_bytes / 1024:.1f} KB"
            else:
                size = f"{size_bytes / (1024 * 1024):.1f} MB"
            
            # Format modified time
            modified = datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            
            # Get display name (remove .log extension)
            display_name = filename
            
            log_files.append({
                "filename": filename,
                "display_name": display_name,
                "size": size,
                "size_bytes": size_bytes,
                "modified": modified,
                "modified_timestamp": stats.st_mtime
            })
        
        # Sort files by modified time (newest first)
        log_files.sort(key=lambda x: x['modified_timestamp'], reverse=True)
        
    except Exception as e:
        logger.error(f"Error getting log files: {str(e)}")
    
    return log_files

def read_log_file(file_path, level='all', search='', date_range='all'):
    """Read log file with filtering options"""
    content = []
    line_count = 0
    
    # Define log levels for filtering
    log_levels = {
        'debug': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        'info': ['INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        'warning': ['WARNING', 'ERROR', 'CRITICAL'],
        'error': ['ERROR', 'CRITICAL'],
        'critical': ['CRITICAL']
    }
    
    # Get levels to include
    include_levels = log_levels.get(level.lower(), None) if level != 'all' else None
    
    # Calculate date range filter
    date_filter = None
    if date_range != 'all':
        today = datetime.datetime.now().date()
        
        if date_range == 'today':
            date_filter = today
        elif date_range == 'yesterday':
            date_filter = today - datetime.timedelta(days=1)
        elif date_range == 'week':
            date_filter = today - datetime.timedelta(days=7)
        elif date_range == 'month':
            date_filter = today - datetime.timedelta(days=30)
    
    # Compile regex for date extraction
    date_regex = re.compile(r'^(\d{4}-\d{2}-\d{2})')
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line_count += 1
                
                # Apply level filter
                if include_levels:
                    level_match = False
                    for lvl in include_levels:
                        if f" - {lvl} - " in line:
                            level_match = True
                            break
                    
                    if not level_match:
                        continue
                
                # Apply search filter
                if search and search.lower() not in line.lower():
                    continue
                
                # Apply date filter
                if date_filter:
                    date_match = date_regex.search(line)
                    if date_match:
                        line_date = datetime.datetime.strptime(date_match.group(1), '%Y-%m-%d').date()
                        
                        if date_range == 'today' and line_date != date_filter:
                            continue
                        elif date_range == 'yesterday' and line_date != date_filter:
                            continue
                        elif date_range in ('week', 'month') and line_date < date_filter:
                            continue
                
                # Add line to content
                content.append(line.rstrip())
        
        return '\n'.join(content), len(content)
    
    except Exception as e:
        logger.error(f"Error reading log file {file_path}: {str(e)}")
        raise

def is_valid_log_file(filename):
    """Validate log filename to prevent directory traversal"""
    # Check for directory traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # Check file extension
    if not filename.endswith('.log'):
        return False
    
    return True 