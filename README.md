# Salesforce Release Note Scraper

A small utility to convert Salesforce release notes into Markdown.

## Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the scraper with the release note URL:
   ```bash
   python scraper.py https://help.salesforce.com/s/articleView?language=en_US&id=release-notes.salesforce_release_notes.htm -o release_notes.md
   ```

The tool fetches the page, extracts the main content, and saves a Markdown version to the specified output file (default: `release_notes.md`).
