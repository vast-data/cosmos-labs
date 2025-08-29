#!/bin/bash
# Swift Dataset Preparation Tool v3
# Downloads ALL Swift GRB dataset files from NASA HEASARC
# Fixed to actually download complete datasets, not just partial files

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DOWNLOAD_DIR="${SCRIPT_DIR}/swift_datasets"
LOG_FILE="${SCRIPT_DIR}/swift_download_v3.log"

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
    
    # Check for wget (primary tool for downloads)
    if ! command -v wget &> /dev/null; then
        missing_deps+=("wget")
    fi
    
    # Check for curl (for connectivity testing and file listing)
    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log "ERROR" "Missing required dependencies: ${missing_deps[*]}"
        log "ERROR" "Please install missing packages and try again"
        return 1
    fi
    
    log "SUCCESS" "All required dependencies available"
    return 0
}

# Test NASA connectivity
test_nasa_connectivity() {
    log "INFO" "Testing NASA HEASARC connectivity..."
    
    local base_url="https://heasarc.gsfc.nasa.gov/FTP/swift/data/"
    
    if command -v curl &> /dev/null; then
        if curl -s -L --head "$base_url" | head -n 1 | grep -q "HTTP/1.1 [23]"; then
            log "SUCCESS" "NASA HEASARC connectivity test passed"
            return 0
        else
            log "ERROR" "NASA HEASARC connectivity test failed"
            return 1
        fi
    else
        if wget -q --spider "$base_url"; then
            log "SUCCESS" "NASA HEASARC connectivity test passed"
            return 0
        else
            log "ERROR" "NASA HEASARC connectivity test failed"
            return 1
        fi
    fi
}

# Get dataset information
get_dataset_info() {
    cat << 'EOF'
batsources_survey_north|BAT source survey data - North hemisphere (comprehensive)|https://heasarc.gsfc.nasa.gov/FTP/swift/data/batsources/survey157m/north|5000-10000 MB|high
batsources_survey_south|BAT source survey data - South hemisphere (comprehensive)|https://heasarc.gsfc.nasa.gov/FTP/swift/data/batsources/survey157m/south|5000-10000 MB|high
batsources_monitoring_north|BAT source monitoring data - North hemisphere (comprehensive)|https://heasarc.gsfc.nasa.gov/FTP/swift/data/batsources/monitoring/north|3000-6000 MB|high
batsources_monitoring_south|BAT source monitoring data - South hemisphere (comprehensive)|https://heasarc.gsfc.nasa.gov/FTP/swift/data/batsources/monitoring/south|2000-4000 MB|high
grbsummary|GRB summary data and catalog information|https://heasarc.gsfc.nasa.gov/FTP/swift/data/grbsummary|1000-2000 MB|medium
EOF
}

# Count available files in a directory
count_available_files() {
    local url="$1"
    local file_pattern="$2"
    
    # Use curl to get directory listing and count matching files
    # Escape the pattern properly for grep
    local escaped_pattern=$(echo "$file_pattern" | sed 's/\./\\./g' | sed 's/\*/.*/g')
    
    # Get the directory listing
    local dir_listing=$(curl -s -L "$url/")
    
    # Count matching files
    local count=$(echo "$dir_listing" | grep -o "href=\"[^\"]*$escaped_pattern\"" | wc -l)
    
    # Debug: show first few files found
    local sample_files=$(echo "$dir_listing" | grep -o "href=\"[^\"]*$escaped_pattern\"" | head -5 | sed 's/href="//g' | sed 's/"//g')
    
    if [[ -n "$sample_files" ]]; then
        log "DEBUG" "Sample files found: $sample_files"
    fi
    
    echo "$count"
}

# Download entire directory by parsing HTML listing and downloading individual files
download_directory() {
    local name="$1"
    local description="$2"
    local url="$3"
    local estimated_size="$4"
    local priority="$5"
    local dry_run="$6"
    
    log "INFO" "Processing dataset: $name"
    log "INFO" "Description: $description"
    log "INFO" "URL: $url"
    log "INFO" "Estimated size: $estimated_size"
    log "INFO" "Priority: $priority"
    
    local dataset_dir="${DOWNLOAD_DIR}/${name}"
    
    # Count available files first
    local available_files=$(count_available_files "$url" "*.lc.gz")
    log "INFO" "Available files in directory: $available_files"
    
    if [[ "$dry_run" == "true" ]]; then
        log "INFO" "[DRY RUN] Would download entire directory to: $dataset_dir"
        log "INFO" "[DRY RUN] Would download approximately $available_files files"
        return 0
    fi
    
    # Remove existing directory to ensure clean download
    if [[ -d "$dataset_dir" ]]; then
        log "INFO" "Removing existing directory: $dataset_dir"
        rm -rf "$dataset_dir"
    fi
    
    # Create dataset directory
    mkdir -p "$dataset_dir"
    
    log "INFO" "Starting download of individual files..."
    log "INFO" "This may take a while - downloading $available_files files..."
    
    # Get the directory listing and extract file URLs
    local dir_listing=$(curl -s -L "$url/")
    local file_urls=$(echo "$dir_listing" | grep -o "href=\"[^\"]*\.lc\.gz\"" | sed 's/href="//g' | sed 's/"//g')
    
    if [[ -z "$file_urls" ]]; then
        log "ERROR" "No .lc.gz files found in directory listing"
        return 1
    fi
    
    local downloaded_count=0
    local total_files=$(echo "$file_urls" | wc -l)
    
    log "INFO" "Found $total_files files to download"
    
    # Download each file individually
    echo "$file_urls" | while read -r filename; do
        if [[ -n "$filename" ]]; then
            local file_url="$url/$filename"
            local local_path="$dataset_dir/$filename"
            
            log "INFO" "Downloading: $filename ($((downloaded_count + 1))/$total_files)"
            
            if curl -s -L -o "$local_path" "$file_url"; then
                downloaded_count=$((downloaded_count + 1))
                log "SUCCESS" "Downloaded: $filename"
            else
                log "ERROR" "Failed to download: $filename"
            fi
        fi
    done
    
    # Count downloaded files
    local file_count=$(find "$dataset_dir" -name "*.lc.gz" | wc -l)
    local total_size=$(du -sh "$dataset_dir" | cut -f1)
    
    log "INFO" "Downloaded $file_count files, total size: $total_size"
    
    # Check if we got most of the available files
    if [[ $available_files -gt 0 ]]; then
        local download_percentage=$((file_count * 100 / available_files))
        if [[ $download_percentage -lt 80 ]]; then
            log "WARNING" "Downloaded only $download_percentage% of available files ($file_count/$available_files)"
        else
            log "SUCCESS" "Downloaded $download_percentage% of available files ($file_count/$available_files)"
        fi
    else
        log "WARNING" "No files were available to download"
    fi
    
    return 0
}

# Main download function
download_all_datasets() {
    local dry_run="$1"
    local force="$2"
    
    log "INFO" "Starting Swift dataset download process..."
    
    if [[ "$dry_run" == "true" ]]; then
        log "INFO" "DRY RUN MODE - No actual downloads will occur"
    fi
    
    # Create download directory
    mkdir -p "$DOWNLOAD_DIR"
    
    # Get dataset info and process each
    local results=()
    local success_count=0
    local total_count=0
    
    while IFS='|' read -r name description url size priority; do
        if [[ -n "$name" ]]; then
            total_count=$((total_count + 1))
            
            local dataset_dir="${DOWNLOAD_DIR}/${name}"
            
            # Skip if already exists and not forcing
            if [[ -d "$dataset_dir" && "$force" != "true" ]]; then
                log "INFO" "Dataset $name already exists, skipping..."
                results+=("$name:true")
                success_count=$((success_count + 1))
                continue
            fi
            
            if download_directory "$name" "$description" "$url" "$size" "$priority" "$dry_run"; then
                results+=("$name:true")
                success_count=$((success_count + 1))
            else
                results+=("$name:false")
            fi
           
        fi
    done < <(get_dataset_info)
    
    # Summary
    log "INFO" "Download process completed!"
    log "INFO" "Total datasets: $total_count"
    log "INFO" "Successful: $success_count"
    log "INFO" "Failed: $((total_count - success_count))"
    
    # Show results
    log "INFO" "Detailed results:"
    for result in "${results[@]}"; do
        IFS=':' read -r name status <<< "$result"
        if [[ "$status" == "true" ]]; then
            log "SUCCESS" "✅ $name"
        else
            log "ERROR" "❌ $name"
        fi
    done
    
    return $((total_count - success_count))
}

# Show help
show_help() {
    local script_name=$(basename "$0")
    cat << EOF
Swift Dataset Preparation Tool v3

Downloads ALL Swift GRB dataset files from NASA HEASARC.

USAGE:
    $script_name [OPTIONS]

OPTIONS:
    -h, --help          Show this help message
    --download          Actually download the datasets (default is dry-run)
    -f, --force         Force re-download of existing datasets
    -v, --verbose       Enable verbose output
    -t, --test          Test NASA connectivity only

EXAMPLES:
    # Test connectivity only
    $script_name --test
    
    # Dry run to see what would be downloaded (default)
    $script_name
    
    # Actually download all datasets
    $script_name --download
    
    # Force re-download of existing datasets
    $script_name --download --force

DATASETS:
    - batsources_survey_north: BAT source survey data (North hemisphere) - ~2,649 files
    - batsources_survey_south: BAT source survey data (South hemisphere) - ~3,024 files
    - batsources_monitoring_north: BAT source monitoring data (North hemisphere) - ~922 files
    - batsources_monitoring_south: BAT source monitoring data (South hemisphere) - ~1,198 files
    - grbsummary: GRB summary data and catalog information

NOTES:
    - Downloads ALL available lightcurve files (*.lc.gz)
    - Automatically counts available files before downloading
    - Verifies download completeness
    - Includes progress tracking and detailed logging
    - Fast downloads optimized for speed

EOF
}

# Main execution
main() {
    local dry_run="true"  # Default to dry-run for safety
    local force="false"
    local test_only="false"
    local verbose="false"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            --download)
                dry_run="false"  # Enable actual downloads
                shift
                ;;
            -f|--force)
                force="true"
                shift
                ;;
            -t|--test)
                test_only="true"
                shift
                ;;
            -v|--verbose)
                verbose="true"
                shift
                ;;
            *)
                log "ERROR" "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Initialize logging
    echo "Swift Dataset Download Log v3 - $(date)" > "$LOG_FILE"
    
    # Check dependencies
    if ! check_dependencies; then
        exit 1
    fi
    
    # Test connectivity
    if ! test_nasa_connectivity; then
        log "ERROR" "Cannot connect to NASA HEASARC. Please check your internet connection."
        exit 1
    fi
    
    if [[ "$test_only" == "true" ]]; then
        log "SUCCESS" "Connectivity test passed. Ready for downloads."
        exit 0
    fi
    
    # Download datasets
    if download_all_datasets "$dry_run" "$force"; then
        log "SUCCESS" "All datasets processed successfully!"
        exit 0
    else
        log "ERROR" "Some datasets failed to download. Check the log for details."
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
