#!/bin/bash
# Swift Dataset Preparation Tool
# Downloads Swift GRB datasets from NASA HEASARC and prepares them for VAST Data platform integration

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DOWNLOAD_DIR="${SCRIPT_DIR}/swift_datasets"
LOG_FILE="${SCRIPT_DIR}/swift_download.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        "INFO")
            echo -e "${BLUE}[INFO]${NC} $message"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[SUCCESS]${NC} $message"
            ;;
        "WARNING")
            echo -e "${YELLOW}[WARNING]${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
    esac
    
    # Also write to log file
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Check if required commands are available
check_dependencies() {
    log "INFO" "Checking system dependencies..."
    
    local missing_deps=()
    
    # Check for curl (for downloads)
    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    fi
    
    # Check for wget (alternative to curl)
    if ! command -v wget &> /dev/null; then
        if [[ ${#missing_deps[@]} -eq 0 ]]; then
            missing_deps+=("wget")
        fi
    fi
    
    # Check for jq (for JSON parsing if needed)
    if ! command -v jq &> /dev/null; then
        log "WARNING" "jq not found - JSON parsing will be limited"
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log "ERROR" "Missing required dependencies: ${missing_deps[*]}"
        log "ERROR" "Please install missing packages and try again"
        return 1
    fi
    
    log "SUCCESS" "All required dependencies available"
    return 0
}

# Download function using curl or wget
download_file() {
    local url="$1"
    local local_path="$2"
    local filename=$(basename "$local_path")
    
    log "INFO" "Downloading: $filename"
    
    # Create directory if it doesn't exist
    mkdir -p "$(dirname "$local_path")"
    
    # Try curl first, then wget
    if command -v curl &> /dev/null; then
        if curl -L -o "$local_path" --progress-bar "$url"; then
            log "SUCCESS" "Downloaded: $filename"
            return 0
        else
            log "ERROR" "Failed to download: $filename"
            return 1
        fi
    elif command -v wget &> /dev/null; then
        if wget -O "$local_path" --progress=bar "$url"; then
            log "SUCCESS" "Downloaded: $filename"
            return 0
        else
            log "ERROR" "Failed to download: $filename"
            return 1
        fi
    else
        log "ERROR" "No download tool available (curl or wget)"
        return 1
    fi
}

# Get dataset information
get_dataset_info() {
    cat << 'EOF'
grbsummary|GRB summary products documentation|https://heasarc.gsfc.nasa.gov/FTP/swift/data/grbsummary/others|1-10 MB|high|README
batsources_survey|BAT source catalog from 157 months of data|https://heasarc.gsfc.nasa.gov/FTP/swift/data/batsources/survey157m/north|100-200 MB|high|swbj0000_5p3251_c_s157.lc.gz,swbj0002_5p0323_c_s157.lc.gz
batsources_monitoring|BAT source monitoring data|https://heasarc.gsfc.nasa.gov/FTP/swift/data/batsources/monitoring/north|200-500 MB|medium|swbj0007_0p7303_o2507.lc.gz,swbj0010_5p1057_o2507.lc.gz
archive_metadata|Archive metadata tables|https://heasarc.gsfc.nasa.gov/FTP/swift/data/other/archive_metadata|10-50 MB|low|swiftgrbba.tdat,swiftguano.tdat
EOF
}

# Download a complete dataset
download_dataset() {
    local dataset_name="$1"
    local dataset_info="$2"
    local dry_run="$3"
    
    # Parse dataset info - format: name|description|url|size_estimate|priority|files
    IFS='|' read -r name description url size_estimate priority files <<< "$dataset_info"
    
    log "INFO" "Processing dataset: $name"
    log "INFO" "Description: $description"
    log "INFO" "Estimated size: $size_estimate"
    
    if [[ "$dry_run" == "true" ]]; then
        log "INFO" "[DRY RUN] Would download $name to ${DOWNLOAD_DIR}/$name"
        return 0
    fi
    
    local dataset_dir="${DOWNLOAD_DIR}/${name}"
    mkdir -p "$dataset_dir"
    
    local success_count=0
    local total_files=0
    
    # Split files by comma and download each
    IFS=',' read -ra file_array <<< "$files"
    total_files=${#file_array[@]}
    
    for filename in "${file_array[@]}"; do
        filename=$(echo "$filename" | xargs)  # Trim whitespace
        local file_url="${url}/${filename}"
        local local_path="${dataset_dir}/${filename}"
        
        if download_file "$file_url" "$local_path"; then
            ((success_count++))
        fi
        
        # Add delay between downloads to be respectful
        sleep 2
    done
    
    local success_rate=$((success_count * 100 / total_files))
    log "INFO" "Dataset $name: $success_count/$total_files files downloaded ($success_rate%)"
    
    # Consider successful if 80%+ files downloaded
    if [[ $success_rate -ge 80 ]]; then
        return 0
    else
        return 1
    fi
}

# Test NASA connectivity
test_nasa_connectivity() {
    log "INFO" "Testing NASA HEASARC connectivity..."
    
    local base_url="https://heasarc.gsfc.nasa.gov/FTP/swift/data/"
    
    if command -v curl &> /dev/null; then
        # Test with curl, following redirects and accepting any 2xx or 3xx status
        if curl -s -L --head "$base_url" | head -n 1 | grep -q "HTTP/1.1 [23]"; then
            log "SUCCESS" "NASA HEASARC connectivity test passed"
            return 0
        else
            log "ERROR" "NASA HEASARC connectivity test failed"
            return 1
        fi
    elif command -v wget &> /dev/null; then
        if wget -q --spider "$base_url"; then
            log "SUCCESS" "NASA HEASARC connectivity test passed"
            return 0
        else
            log "ERROR" "NASA HEASARC connectivity test failed"
            return 1
        fi
    else
        log "ERROR" "No tool available to test connectivity"
        return 1
    fi
}

# Main download function
download_all_datasets() {
    local dry_run="$1"
    local force="$2"
    
    log "INFO" "Starting Swift dataset download process..."
    
    # Create download directory
    mkdir -p "$DOWNLOAD_DIR"
    
    # Get dataset info and process each
    local results=()
    local line_num=0
    
    while IFS= read -r line; do
        if [[ -n "$line" ]]; then
            IFS='|' read -r name description url size priority files <<< "$line"
            
            local dataset_dir="${DOWNLOAD_DIR}/${name}"
            
            # Skip if already exists and not forcing
            if [[ -d "$dataset_dir" && "$force" != "true" ]]; then
                log "INFO" "Dataset $name already exists, skipping..."
                results+=("$name:true")
                continue
            fi
            
            if download_dataset "$name" "$line" "$dry_run"; then
                results+=("$name:true")
            else
                results+=("$name:false")
            fi
        fi
    done < <(get_dataset_info)
    
    # Print summary
    echo
    echo "============================================================"
    echo "SWIFT DATASET PROCESSING SUMMARY"
    echo "============================================================"
    
    echo
    echo "DOWNLOAD RESULTS:"
    for result in "${results[@]}"; do
        IFS=':' read -r name success <<< "$result"
        if [[ "$success" == "true" ]]; then
            echo "  $name: ✅ SUCCESS"
        else
            echo "  $name: ❌ FAILED"
        fi
    done
    
    echo
    echo "NEXT STEPS:"
    echo "  1. Review downloaded datasets in 'swift_datasets/' directory"
    echo "  2. Use datasets for lab exercises"
    echo "  3. Integrate with VAST systems as needed"
    
    if [[ "$dry_run" == "true" ]]; then
        echo
        echo "⚠️  This was a DRY RUN - no actual changes were made"
    fi
}

# Show help message
show_help() {
    local script_name="$1"
    cat << EOF
Swift Dataset Preparation Tool

Usage: $script_name [OPTIONS]

OPTIONS:
    --download             Download all Swift datasets
    --dry-run              Show what would be done without actually doing it
    --force                Force re-download of existing datasets
    --help                 Show this help message

EXAMPLES:
    # Download all datasets
    $script_name --download
    
    # Test run without downloading
    $script_name --dry-run
    
    # Force re-download existing datasets
    $script_name --download --force

NOTE: Running without options will show this help message.
      Use --dry-run to test what the script would do.
      Use --download to actually download the datasets.
      This tool prepares datasets locally for later VAST upload.
EOF
}

# Main function
main() {
    # Parse command line arguments
    local dry_run=false
    local force=false
    local download=false
    
    # Default to help if no arguments provided
    if [[ $# -eq 0 ]]; then
        show_help "$0"
        exit 0
    fi
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --download)
                download=true
                shift
                ;;
            --dry-run)
                dry_run=true
                shift
                ;;
            --force)
                force=true
                shift
                ;;
            --help)
                show_help "$0"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Initialize log file
    echo "Swift Dataset Preparation Log - $(date)" > "$LOG_FILE"
    echo "========================================" >> "$LOG_FILE"
    
    log "INFO" "Swift Dataset Preparation Tool started"
    log "INFO" "Project directory: $PROJECT_DIR"
    log "INFO" "Download directory: $DOWNLOAD_DIR"
    log "INFO" "Log file: $LOG_FILE"
    
    # Check dependencies
    if ! check_dependencies; then
        exit 1
    fi
    
    # Test NASA connectivity
    if ! test_nasa_connectivity; then
        log "ERROR" "Cannot proceed without NASA connectivity"
        exit 1
    fi
    
    # Download datasets
    download_all_datasets "$dry_run" "$force"
    
    log "INFO" "Swift dataset processing complete"
}

# Run main function with all arguments
main "$@"
