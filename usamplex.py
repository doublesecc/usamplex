import random
import argparse
import pandas as pd
import time
import sys

# ANSI escape codes for color formatting
CYAN = '\033[96m'
RED = '\033[91m'
GREEN = '\033[92m'
RESET = '\033[0m'
STATUS_BAR = '\033[1;33m'  # Yellow color for status bar

def print_banner(disable_banner):
    """Print the ASCII banner if disable_banner is False."""
    if not disable_banner:
        banner = """

               .-')     ('-.     _   .-')      _ (`-.              ('-.  ) (`-.      
              ( OO ).  ( OO ).-.( '.( OO )_   ( (OO  )           _(  OO)  ( OO ).    
 ,--. ,--.   (_)---\_) / . --. / ,--.   ,--.)_.`     \ ,--.     (,------.(_/.  \_)-. 
 |  | |  |   /    _ |  | \-.  \  |   `.'   |(__...--'' |  |.-')  |  .---' \  `.'  /  
 |  | | .-') \  :` `..-'-'  |  | |         | |  /  | | |  | OO ) |  |      \     /\  
 |  |_|( OO ) '..`''.)\| |_.'  | |  |'.'|  | |  |_.' | |  |`-' |(|  '--.    \   \ |  
 |  | | `-' /.-._)   \ |  .-.  | |  |   |  | |  .___.'(|  '---.' |  .--'   .'    \_) 
('  '-'(_.-' \       / |  | |  | |  |   |  | |  |      |      |  |  `---. /  .'.  \  
  `-----'     `-----'  `--' `--' `--'   `--' `--'      `------'  `------''--'   '--' 

"""
        print(banner)

def read_file_lines(file_path, exclude_keywords=None):
    """Read lines from a file with error handling for encoding issues and support for Excel files."""
    try:
        if file_path.lower().endswith(('.xls', '.xlsx')):
            # Handle Excel files
            df = pd.read_excel(file_path, engine='openpyxl')
            all_lines = df.apply(lambda row: ','.join(row.values.astype(str)), axis=1).tolist()
            original_df = df  # Keep the original DataFrame for structure
        else:
            # Handle text files
            encodings = ['utf-8', 'latin-1']  # Try these encodings
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        all_lines = file.readlines()
                    break
                except UnicodeDecodeError:
                    print(f"{RED}[-] Failed to read the file with encoding {encoding}. Trying the next encoding.{RESET}")
            else:
                raise ValueError("Failed to read the file with all attempted encodings.")
    except Exception as e:
        print(f"{RED}[-] Error: {e}{RESET}")
        raise
    
    # Filter out lines containing any of the exclude_keywords if provided
    if exclude_keywords:
        exclude_keywords = [kw.lower() for kw in exclude_keywords]  # Normalize to lower case
        all_lines = [line for line in all_lines if not any(keyword in line.lower() for keyword in exclude_keywords)]
    
    return all_lines, original_df if 'original_df' in locals() else None

def write_lines_to_file(file_path, lines, original_df=None, verbose=False):
    """Write lines to a file in CSV format, ensuring proper comma separation."""
    try:
        if file_path.lower().endswith(('.xls', '.xlsx')):
            # Handle Excel files by writing to CSV
            if original_df is not None:
                num_cols = len(original_df.columns)
                data = [line.split(',', num_cols - 1) for line in lines]
                new_df = pd.DataFrame(data, columns=original_df.columns)
                new_df.to_csv(file_path, index=False, header=False)
        else:
            # Handle text files
            with open(file_path, 'w') as file:
                for line in lines:
                    file.write(line if line.endswith('\n') else line + '\n')
        if verbose:
            print(f"{CYAN}[~] Successfully wrote to {file_path}{RESET}")
    except Exception as e:
        print(f"{RED}[-] Error writing to file: {e}{RESET}")
        raise

def print_lines_to_stdout(lines):
    """Print lines to stdout with [~] prefix in cyan."""
    for line in lines:
        print(f"{CYAN}[~] {line.strip()}{RESET}")

def print_status_bar(start_time):
    """Print a status bar if the program takes longer than 2 seconds to run."""
    elapsed_time = time.time() - start_time
    if elapsed_time > 2:
        print(f"{STATUS_BAR}[+] Processing...{RESET}", end='\r')
        sys.stdout.flush()
        while time.time() - start_time < 5:  # Status bar active for up to 5 seconds
            elapsed_time = time.time() - start_time
            if elapsed_time > 2:
                sys.stdout.write(f"{STATUS_BAR}[+] Processing...{RESET}")
                sys.stdout.flush()
                time.sleep(0.5)
        print()  # Move to the next line after status bar

def select_lines(input_file, num_lines, output_file_selected, output_file_remaining, exclude_keywords=None, verbose=False, disable_banner=False):
    # Record the start time
    start_time = time.time()
    
    # Print banner if not disabled
    print_banner(disable_banner)
    
    # Read all lines from the input file
    all_lines, original_df = read_file_lines(input_file, exclude_keywords)
    
    # Print status bar if necessary
    print_status_bar(start_time)
    
    # Check if there are enough unique lines in the file
    if len(set(all_lines)) < num_lines:
        print(f"{RED}[-] The file does not contain enough unique lines after filtering.{RESET}")
        return
    
    # Select `num_lines` unique lines randomly
    unique_lines = list(set(all_lines))  # Remove duplicates
    selected_lines = random.sample(unique_lines, num_lines)
    
    # Determine the remaining lines
    remaining_lines = set(unique_lines) - set(selected_lines)
    
    # Write selected lines to the output file
    write_lines_to_file(output_file_selected, selected_lines, original_df, verbose)
    
    # Write remaining lines to the second output file
    write_lines_to_file(output_file_remaining, remaining_lines, original_df, verbose)
    
    # Print to stdout if verbose
    if verbose:
        if exclude_keywords:
            print(f"{CYAN}[~] Excluded lines containing the keywords: {', '.join(exclude_keywords)}{RESET}\n")
        print("\nSelected lines:")
        print_lines_to_stdout(selected_lines)
        print("\nRemaining lines:")
        print_lines_to_stdout(remaining_lines)
    
    print(f"{GREEN}[+] Selected lines saved to '{output_file_selected}'.{RESET}")
    print(f"{GREEN}[+] Remaining lines saved to '{output_file_remaining}'.{RESET}")

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Select a number of unique lines randomly from a file (text or Excel) and save them to two new files.')
    
    # Optional arguments with short options
    parser.add_argument('-f', '--input_file', type=str, required=True, help='The input file to read from.')
    parser.add_argument('-n', '--num_lines', type=int, required=True, help='The number of unique lines to randomly select and extract.')
    parser.add_argument('-x', '--output_file_selected', type=str, required=True, help='The file to save the extracted lines.')
    parser.add_argument('-r', '--output_file_remaining', type=str, required=True, help='The file to save the remaining non extracted lines.')
    parser.add_argument('-e', '--exclude_keywords', type=str, nargs='*', default=None, help='Keywords to exclude lines containing any of these keywords.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print selected and remaining lines to stdout.')
    parser.add_argument('-d', '--disable-banner', action='store_true', help='Disable the ASCII banner display.')

    args = parser.parse_args()
    
    # Call the function with the arguments
    select_lines(args.input_file, args.num_lines, args.output_file_selected, args.output_file_remaining, args.exclude_keywords, args.verbose, args.disable_banner)

if __name__ == "__main__":
    main()
