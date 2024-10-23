"""
    Plugin for ResolveURL
    Copyright (C) 2023 shellc0de

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from six.moves import urllib_parse
from resolveurl.lib import helpers
from resolveurl.plugins.__resolve_generic__ import ResolveGeneric
import xbmc
import requests
import os
import xbmcvfs
from xbmcaddon import Addon
ADDON_DATA_PATH = xbmcvfs.translatePath(Addon().getAddonInfo('profile'))
m3ufile = os.path.join(ADDON_DATA_PATH, 'stream.m3u8')

class StreamWishResolver(ResolveGeneric):
    name = 'StreamWish'
    domains = [
        'streamwish.com', 'streamwish.to', 'ajmidyad.sbs', 'khadhnayad.sbs', 'yadmalik.sbs',
        'hayaatieadhab.sbs', 'kharabnahs.sbs', 'atabkhha.sbs', 'atabknha.sbs', 'atabknhk.sbs',
        'atabknhs.sbs', 'abkrzkr.sbs', 'abkrzkz.sbs', 'wishembed.pro', 'mwish.pro', 'strmwis.xyz',
        'awish.pro', 'dwish.pro', 'vidmoviesb.xyz', 'embedwish.com', 'cilootv.store', 'uqloads.xyz',
        'tuktukcinema.store', 'doodporn.xyz', 'ankrzkz.sbs', 'volvovideo.top', 'streamwish.site',
        'wishfast.top', 'ankrznm.sbs', 'sfastwish.com', 'eghjrutf.sbs', 'eghzrutw.sbs',
        'playembed.online', 'egsyxurh.sbs', 'egtpgrvh.sbs', 'flaswish.com', 'obeywish.com',
        'cdnwish.com', 'javsw.me', 'cinemathek.online', 'trgsfjll.sbs', 'fsdcmo.sbs',
        'anime4low.sbs', 'mohahhda.site', 'ma2d.store', 'dancima.shop', 'swhoi.com',
        'gsfqzmqu.sbs', 'jodwish.com', 'swdyu.com', 'strwish.com', 'asnwish.com',
        'wishonly.site', 'playerwish.com', 'katomen.store', 'hlswish.com'
    ]
    pattern = r'(?://|\.)((?:(?:stream|flas|obey|sfast|str|embed|[mad]|cdn|asn|player|hls)?wish(?:embed|fast|only)?|ajmidyad|' \
              r'atabkhha|atabknha|atabknhk|atabknhs|abkrzkr|abkrzkz|vidmoviesb|kharabnahs|hayaatieadhab|' \
              r'cilootv|tuktukcinema|doodporn|ankrzkz|volvovideo|strmwis|ankrznm|yadmalik|khadhnayad|' \
              r'eghjrutf|eghzrutw|playembed|egsyxurh|egtpgrvh|uqloads|javsw|cinemathek|trgsfjll|fsdcmo|' \
              r'anime4low|mohahhda|ma2d|dancima|swhoi|gsfqzmqu|jodwish|swdyu|katomen)' \
              r'\.(?:com|to|sbs|pro|xyz|store|top|site|online|me|shop))/(?:e/|f/|d/)?([0-9a-zA-Z$:/.]+)'

    def get_media_url(self, host, media_id, subs=False):
        xbmc.log("Starting get_media_url with host: {} and media_id: {}".format(host, media_id), level=xbmc.LOGDEBUG)
        if '$$' in media_id:
            media_id, referer = media_id.split('$$')
            referer = urllib_parse.urljoin(referer, '/')
            xbmc.log("Referer URL: " + referer, level=xbmc.LOGDEBUG)
        else:
            referer = False

        url = helpers.get_media_url(
            self.get_url(host, media_id),
            patterns=[r'''sources:\s*\[{file:\s*["'](?P<url>[^"']+)'''],
            generic_patterns=False,
            referer=referer,
            subs=subs
        )
        xbmc.log("Resolved URL: " + str(url), level=xbmc.LOGDEBUG)

        if url:
            download_link, headers = url.split('|')
            headers_dict = self.parse_headers(headers)
            master_m3u8_path = self.download_master_m3u8(download_link, headers_dict)

            return master_m3u8_path
        xbmc.log("No URL resolved.", level=xbmc.LOGERROR)
        return None

    def parse_headers(self, headers):
        """Parses headers from a string to a dictionary."""
        xbmc.log("Parsing headers: " + headers, level=xbmc.LOGDEBUG)
        return dict(header.split('=') for header in headers.split('&'))

    def download_master_m3u8(self, download_link, headers):
        """Downloads the master M3U8 file and modifies it."""
        xbmc.log("Downloading master M3U8 from: " + download_link, level=xbmc.LOGDEBUG)
        response = requests.get(download_link, headers=headers)
        if response.status_code == 200:
            xbmc.log("Successfully downloaded master M3U8", level=xbmc.LOGDEBUG)
            new_download_link = download_link.split("master.m3u8")[0]
            
            # Hier konvertieren wir die Bytes in einen String
            content_str = response.content.decode('utf-8')
            xbmc.log("m3ufile:"+ content_str)
            m3u8_link = self.extract_m3u8_links(content_str)
            if m3u8_link:
                xbmc.log("Extracted M3U8 link: " + str(m3u8_link), level=xbmc.LOGDEBUG)
                new_download_link += m3u8_link
                response = requests.get(new_download_link, headers=headers)
                if response.status_code == 200:
                    xbmc.log("Successfully downloaded secondary M3U8", level=xbmc.LOGDEBUG)
                    return self.modify_m3u(response.content, new_download_link)
                else:
                    xbmc.log("Failed to download secondary M3U8, status code: {}".format(response.status_code), level=xbmc.LOGERROR)
            else:
                xbmc.log("No M3U8 links found in the master file.", level=xbmc.LOGERROR)
        else:
            xbmc.log("Failed to download master M3U8, status code: {}".format(response.status_code), level=xbmc.LOGERROR)
        return None

    def extract_m3u8_links(self, content):
        """Extracts M3U8 links from the M3U content."""
        return content.splitlines()[2]


    def modify_m3u(self, content, download_link):
        """Modifies the M3U content and replaces FQDNs."""
        xbmc.log("Modifying M3U content.", level=xbmc.LOGDEBUG)
        neuer_fqdn = urllib_parse.urlparse(download_link).netloc
        xbmc.log("New FQDN: " + neuer_fqdn, level=xbmc.LOGDEBUG)
        
        existing_fqdn = self.extract_existing_fqdn(content)
        xbmc.log("Existing FQDN found: " + str(existing_fqdn), level=xbmc.LOGDEBUG)

        if existing_fqdn:
            modified_content = content.replace(existing_fqdn.encode('utf-8'), neuer_fqdn.encode('utf-8'))

            xbmc.log("Saving modified M3U file to: " + m3ufile, level=xbmc.LOGDEBUG)
            with open(m3ufile, 'wb') as file:
                file.write(modified_content)

            xbmc.log("Modified M3U file saved successfully.", level=xbmc.LOGDEBUG)
            return m3ufile

        xbmc.log("No existing FQDN found to replace.", level=xbmc.LOGERROR)
        return None

    def extract_existing_fqdn(self, content):
        """Extracts the first FQDN found in the M3U content."""
        lines = content.decode('utf-8').splitlines()
        for line in lines:
            parsed_url = urllib_parse.urlparse(line)
            if parsed_url.netloc:
                xbmc.log("Found existing FQDN: " + parsed_url.netloc, level=xbmc.LOGDEBUG)
                return parsed_url.netloc
        xbmc.log("No FQDN found in content.", level=xbmc.LOGERROR)
        return None

    def get_url(self, host, media_id):
        return self._default_get_url(host, media_id, template='https://{host}/e/{media_id}')
