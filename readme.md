# CVE-2021-40346: HAProxy HTTP Request Smuggling - ACL Bypass

## Overview

This project demonstrates **CVE-2021-40346**, a critical integer overflow vulnerability in HAProxy that enables HTTP Request Smuggling attacks to bypass security controls.

**CVSSv3 Score:** 8.6 (High)  

---

## What is CVE-2021-40346?

CVE-2021-40346 is an **integer overflow vulnerability** in HAProxy's HTTP header parsing logic. When a header name exceeds 255 bytes, the length value overflows from an 8-bit field, causing HAProxy to misinterpret the header during request forwarding.