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
