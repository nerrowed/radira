#!/usr/bin/env python3
"""
Contoh Sederhana Testing XSS
Simple XSS Testing Example
===========================

HANYA UNTUK TUJUAN EDUKASI
FOR EDUCATIONAL PURPOSES ONLY

Contoh ini menunjukkan cara kerja dasar XSS testing
This example shows the basic workings of XSS testing
"""

import requests
from bs4 import BeautifulSoup


def test_simple_xss(url, payload):
    """
    Fungsi sederhana untuk menguji XSS
    Simple function to test for XSS

    Args:
        url: Target URL (harus memiliki parameter, misal: ?search=test)
        payload: XSS payload untuk diuji
    """
    print(f"\n{'='*60}")
    print(f"Testing URL: {url}")
    print(f"Payload: {payload}")
    print(f"{'='*60}\n")

    try:
        # Kirim request dengan payload
        # Send request with payload
        response = requests.get(url, timeout=10)

        # Cek apakah payload muncul di response
        # Check if payload appears in response
        if payload in response.text:
            print("✗ VULNERABLE: Payload ditemukan di response!")
            print("  Payload TIDAK di-escape dengan benar")
            print("  (Payload NOT properly escaped)")

            # Tampilkan konteks dimana payload muncul
            # Show context where payload appears
            soup = BeautifulSoup(response.text, 'html.parser')
            print(f"\n  Response snippet:")

            # Cari teks yang mengandung payload
            text_content = response.text
            payload_index = text_content.find(payload)
            if payload_index != -1:
                start = max(0, payload_index - 50)
                end = min(len(text_content), payload_index + len(payload) + 50)
                snippet = text_content[start:end]
                print(f"  ...{snippet}...")

            return True
        else:
            print("✓ SAFE: Payload tidak ditemukan atau di-escape dengan benar")
            print("  (Payload not found or properly escaped)")
            return False

    except requests.RequestException as e:
        print(f"Error: {e}")
        return None


def demonstrate_xss_payloads():
    """
    Demonstrasi berbagai jenis XSS payload
    Demonstration of various XSS payload types
    """
    print("\n" + "="*60)
    print("DEMONSTRASI XSS PAYLOADS")
    print("XSS PAYLOADS DEMONSTRATION")
    print("="*60)

    payloads = {
        "Basic Script Tag": "<script>alert('XSS')</script>",
        "Image Tag with onerror": "<img src=x onerror=alert('XSS')>",
        "SVG with onload": "<svg/onload=alert('XSS')>",
        "Input with autofocus": "<input onfocus=alert('XSS') autofocus>",
        "Body with onload": "<body onload=alert('XSS')>",
    }

    for name, payload in payloads.items():
        print(f"\n{name}:")
        print(f"  Payload: {payload}")
        print(f"  Penjelasan: Mencoba execute JavaScript melalui {name.lower()}")
        print(f"  Explanation: Attempts to execute JavaScript via {name.lower()}")


def demonstrate_prevention():
    """
    Demonstrasi cara mencegah XSS
    Demonstration of XSS prevention
    """
    print("\n" + "="*60)
    print("CARA MENCEGAH XSS")
    print("XSS PREVENTION METHODS")
    print("="*60)

    print("""
1. INPUT VALIDATION (Validasi Input)
   - Validasi semua input dari user
   - Gunakan whitelist, bukan blacklist

2. OUTPUT ENCODING (Encoding Output)
   - HTML Entity Encoding: &lt; &gt; &quot; &#x27; &amp;
   - JavaScript Encoding: \\x3C \\x3E
   - URL Encoding: %3C %3E

3. CONTENT SECURITY POLICY (CSP)
   - Header: Content-Security-Policy
   - Batasi sumber JavaScript yang diizinkan

4. HTTP-ONLY COOKIES
   - Set HttpOnly flag pada cookies
   - Mencegah akses cookie via JavaScript

5. USE FRAMEWORKS WITH AUTO-ESCAPING
   - React, Angular, Vue.js
   - Template engines dengan auto-escape

Contoh Python (Flask):
----------------------
from flask import escape

@app.route('/search')
def search():
    query = request.args.get('q', '')
    # Escape output
    safe_query = escape(query)
    return f"Hasil pencarian: {safe_query}"

Contoh Python (manual escaping):
---------------------------------
import html

user_input = "<script>alert('XSS')</script>"
safe_output = html.escape(user_input)
# Output: &lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;
    """)


def main():
    """Main function dengan contoh penggunaan"""

    print("""
╔══════════════════════════════════════════════════════════════════╗
║                 XSS TESTING - EDUCATIONAL EXAMPLE                 ║
║                 CONTOH EDUKASI - TESTING XSS                      ║
╚══════════════════════════════════════════════════════════════════╝

⚠️  PERINGATAN / WARNING:
   Hanya gunakan pada sistem yang Anda miliki atau memiliki izin!
   Only use on systems you own or have written permission to test!
    """)

    # Demonstrasi payloads
    demonstrate_xss_payloads()

    # Demonstrasi pencegahan
    demonstrate_prevention()

    print("\n" + "="*60)
    print("CONTOH PENGGUNAAN / USAGE EXAMPLE")
    print("="*60)
    print("""
# Test XSS pada URL dengan parameter
# Test XSS on URL with parameter

from xss_simple_example import test_simple_xss

# Contoh URL vulnerable (untuk testing)
# Example vulnerable URL (for testing)
test_url = "http://testphp.vulnweb.com/search.php?test=<script>alert('XSS')</script>"

# Test dengan berbagai payload
# Test with various payloads
payloads = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
    "<svg/onload=alert('XSS')>"
]

for payload in payloads:
    # Replace parameter value dengan payload
    url = test_url.replace("test=", f"test={payload}")
    test_simple_xss(url, payload)
    """)

    print("\n" + "="*60)
    print("Untuk testing lengkap, gunakan:")
    print("For full testing, use:")
    print("  python xss_vulnerability_tester.py -u <URL>")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
