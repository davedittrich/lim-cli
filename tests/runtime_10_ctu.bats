load test_helper

# See definition of LIM in test_helpers.bash for why "main" is used
# in tests.

setup_file() {
    true
}

teardown_file() {
    true
}

setup() {
    true
}

teardown() {
    true
}

####  ctu list  ####

@test "\"lim -q ctu list CTU-Malware-Capture-Botnet-48\" works" {
    run bash -c "$LIM -q ctu list CTU-Malware-Capture-Botnet-48"
    assert_output '+----------------+-------------------------------+---------+
| Infection_Date | Capture_Name                  | Malware |
+----------------+-------------------------------+---------+
| 2011-08-10     | CTU-Malware-Capture-Botnet-48 | Sogou   |
+----------------+-------------------------------+---------+'
}

@test "\"lim -q ctu list Botnet-48\" works" {
    run bash -c "$LIM -q ctu list Botnet-48"
    assert_output '+----------------+-------------------------------+---------+
| Infection_Date | Capture_Name                  | Malware |
+----------------+-------------------------------+---------+
| 2011-08-10     | CTU-Malware-Capture-Botnet-48 | Sogou   |
+----------------+-------------------------------+---------+'
}

@test "\"lim -q ctu list Botnet-488888\" fails" {
    run bash -c "$LIM -q ctu list Botnet-48888"
    assert_failure
}

@test "\"lim -q ctu list --name-includes iot\" works" {
    run bash -c "$LIM -q ctu list --name-includes iot"
    assert_output --partial 'IoT'
}

@test "\"lim -q ctu list --name-includes foobar\" fails" {
    run bash -c "$LIM -q ctu list --name-includes foobar"
    assert_failure
}

@test "\"lim -q ctu list --description-includes ransom\" works" {
    run bash -c "$LIM -q ctu list --description-includes ransom"
    assert_output --partial 'WannaCry'
}

@test "\"lim -q ctu list --description-includes washes_windows\" fails" {
    run bash -c "$LIM -q ctu list --description-includes washes_windows"
    assert_failure
}

@test "\"lim -q ctu list --malware-includes rbot\" works" {
    run bash -c "$LIM -q ctu list --malware-includes rbot"
    assert_output --partial 'RBot'
}

@test "\"lim -q ctu list --hash 8a71965cba1d3596745f63e3d8a5ac3f\" works" {
    run bash -c "$LIM -q ctu list --hash 8a71965cba1d3596745f63e3d8a5ac3f"
    assert_output --partial 'CTU-Malware-Capture-Botnet-48'
}

@test "\"lim -q ctu list --hash 38e2e22448a4856736d36823d4b4fe1181bcc189cae6d9840319c2890569197e\" works" {
    run bash -c "$LIM -q ctu list --hash 38e2e22448a4856736d36823d4b4fe1181bcc189cae6d9840319c2890569197e"
    assert_output --partial 'CTU-Malware-Capture-Botnet-48'
}

@test "\"lim -q ctu list --hash 00000000\" fails" {
    run bash -c "$LIM -q ctu list --hash 00000000"
    assert_failure
}

####  ctu get  ####

@test "\"lim -q ctu get Botnet-114-1 pcap\" gets PCAP file in subdir" {
    run bash -c "[ -f CTU-Malware-Capture-Botnet-114-1/2015-04-09_capture-win2.pcap ] || $LIM -q ctu get Botnet-114-1 pcap"
    [ -d CTU-Malware-Capture-Botnet-114-1 ]
    [ -f CTU-Malware-Capture-Botnet-114-1/2015-04-09_capture-win2.pcap ]
}

@test "\"lim -q ctu get Botnet-114-1 pcap --no-subdir \" gets PCAP file to cwd" {
    run bash -c "[ -f 2015-04-09_capture-win2.pcap ] || $LIM -q ctu get Botnet-114-1 pcap --no-subdir"
    [ -f 2015-04-09_capture-win2.pcap ]
}

####  ctu show  ####

@test "\"lim -q ctu show CTU-Malware-Capture-Botnet-42\" works" {
    run bash -c "$LIM -q ctu show CTU-Malware-Capture-Botnet-42"
    assert_output '+----------------+------------------------------------------------------------------------+
| Field          | Value                                                                  |
+----------------+------------------------------------------------------------------------+
| Infection_Date | 2011-08-10                                                             |
| Capture_Name   | CTU-Malware-Capture-Botnet-42                                          |
| Malware        | Neeris                                                                 |
| MD5            | bf08e6b02e00d2bc6dd493e93e69872f                                       |
| SHA256         | 527da5fd4e501765cdd1bccb2f7c5ac76c0b22dfaf7c24e914df4e1cb8029d71       |
| Capture_URL    | https://mcfp.felk.cvut.cz/publicDatasets/CTU-Malware-Capture-Botnet-42 |
| ZIP            | Neris.exe.zip                                                          |
| LABELED        | None                                                                   |
| BINETFLOW      | None                                                                   |
| PCAP           | botnet-capture-20110810-neris.pcap                                     |
| WEBLOGNG       | None                                                                   |
+----------------+------------------------------------------------------------------------+'
}

####  ctu stats  ####

@test "\"lim -q ctu stats\" defaults to date" {
    run bash -c "$LIM -q ctu stats 2>/dev/null"
    assert_output --partial 'Infection_Date'
}

@test "\"lim -q ctu stats SHA256\" works" {
    run bash -c "$LIM -q ctu stats SHA256 2>/dev/null | head -n 3"
    assert_output '+------------------------------------------------------------------+-------+
| SHA256                                                           | Count |
+------------------------------------------------------------------+-------+'
}

# vim: set ts=4 sw=4 tw=0 et :
