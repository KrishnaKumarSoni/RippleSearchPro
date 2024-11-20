I want a python flask setup (with basic black and white tailwind frontend). 

Requirements: 
[PHASE 1]
1. User should be able to enter any search query. 
2. After user enters their search query, we should use web scraping SPECIFICALLY FOR GOOGLE PLACES (NOT MAPS).
3. We should one by one click each list item till the page ends and pick up all their available details (Name, Phone Number, Website, Address, Ratings, Reviews, Timings) from the detailed modal that opens up.
4. output should be a csv file that can be downloaded. 

KNOWN CAVEATS:
1. GOOGLE PLACES REQUIRES US TO PASS LOCATION IN THE PARAMETER
2. GOOGLE PLACES WEBSITE SELECTORS ARE DYNAMIC. 
3. WE NEED NON HEADLESS MODE TO UNDERSTAND THE HAPPENINGS. DO NOT USE HEADLESS MODE.

[PHASE 2]
4. Then visit their website (if available), scrape all text and figure out / extract the contact details - Phone Number & Email.
5. This should be appended to the output fields without duplicating the existing fields.

[PHASE 3]
6. All background processes (API calls / logs) should be neatly visible on the frontend.
7. All extracted data should be visible in a table on the front end with row by row real time data updating as we are extracting / generating it. Table should include row numbers & appropriate column names. 
8. Table should have two key actions: Clear, Export
9. Table rows should be arranged such that the most recently extracted thing shows on the top. 
10. The tool is called Ripple Search. 
11. Don't make this too complex. Keep it simple. Use web scraping to get the data from google places. 

start implementation from backend.

I want to use Google Fonts. I like Inter Tight for body and Plus Jakarta Sans only for the headings. 


Here's a detailed breakdown of what places_scraper.py should do:
Initialization & Setup
Create a scraper class that can run in non-headless mode
Set up basic configurations for output directory and browser settings
Initialize state tracking for modal and page management
Handle browser context and cleanup properly
Search Query Processing
Accept two inputs: search query and location
Construct proper Google Places URL (not Maps) with local search parameter
Navigate to the search results page
Wait for the page to load completely and stabilize
List Item Processing
Find and wait for all business listings on the page (typically 20 per page)
Extract basic information from each listing (name and reference)
Track seen items to avoid duplicates
Process items one by one in sequence
Modal Interaction & Data Extraction
For each business listing:
Scroll the item into view
Click to open its details modal
Wait for modal to fully load
Extract comprehensive details:
Business name
Phone number
Website URL
Physical address
Rating (if available)
Reviews (up to 5 recent ones)
Operating hours/timings
Close modal properly
Verify return to listing view
Handle any extraction failures with retries (3 attempts)
Pagination Handling
Check for next page button after processing all items on current page
If next page exists, click and wait for new items to load
Continue extraction process for new page
Repeat until no more pages are available
Data Management
Store all extracted data in a structured format
Maintain unique entries using business names as keys
Track extraction timestamp for each entry
Prepare data for CSV export
Error Handling & Recovery
Handle dynamic selector changes gracefully
Recover from modal state issues
Handle network timeouts and page load failures
Log all errors and extraction status
Maintain session stability across pages
Output Generation
Format extracted data according to specified columns
Generate timestamped CSV files
Handle special characters and formatting in business data
Ensure all fields are properly escaped for CSV format
Please use accurate selectors. 