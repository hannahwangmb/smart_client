# Smart Client

Performed HTTP/HTTPS connection analysis using Python. Used socket and SSL to connect to servers,
successfully handled redirects and detected password-protected and h2-supported sites

Author: hannahwangmb@uvic.ca

Date: Sep. 29, 2023

## Usage

To run the SmartClient program, use the following command:

    $ python3 SmartClient.py <url>

Replace '<url>' with a valid URL. The URL should at least contain a valid domain name.

Example:

    $ python3 SmartClient.py www.google.com
