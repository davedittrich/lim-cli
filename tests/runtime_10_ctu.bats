load test_helper

# See definition of LIM in test_helpers.bash for why "main" is used
# in tests.

setup_file() {
    export NETWORKING=$(ping -c 3 8.8.8.8 | grep -q ' 0% packet loss' && echo "UP" || echo "DOWN")
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

@test "\"lim -q ctu list Malware-Botnet-90 Botnet-137-1 IoT-49-1\" works" {
    run bash -c "$LIM ctu list Malware-Botnet-90 Botnet-137-1 IoT-49-1"
    assert_output "+----------------+----------------------------------+-----------+
| Infection_Date | Capture_Name                     | Malware   |
+----------------+----------------------------------+-----------+
| 2009-09-07     | CTU-Malware-Capture-Botnet-90    | Conficker |
| 2015-10-04     | CTU-Malware-Capture-Botnet-137-1 | bab0      |
| 2019-02-28     | CTU-IoT-Malware-Capture-49-1     | Mirai     |
+----------------+----------------------------------+-----------+"
}

@test "\"lim -q ctu list 34-1\" works" {
    run bash -c "$LIM -q ctu list 34-1"
    assert_output --partial 'CTU-IoT-Malware-Capture-34-1'
}

@test "\"lim -q ctu list IoT-34-1\" works" {
    run bash -c "$LIM -q ctu list IoT-34-1"
    assert_output --partial 'CTU-IoT-Malware-Capture-34-1'
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

@test "\"lim -q ctu list --name-includes iot --date-starting 2018-10-01 --date-ending 2018-10-30\" works" {
    run bash -c "$LIM -q ctu list --name-includes iot --date-starting 2018-10-01 --date-ending 2018-10-30"
    assert_success
    assert_output "+----------------+------------------------------+---------+
| Infection_Date | Capture_Name                 | Malware |
+----------------+------------------------------+---------+
| 2018-10-02     | CTU-IoT-Malware-Capture-20-1 | Torii   |
| 2018-10-03     | CTU-IoT-Malware-Capture-21-1 | Torii   |
+----------------+------------------------------+---------+"
}

@test "\"lim -q ctu list --name-includes IoT -a --malware-includes muhstik -f csv\" works" {
    run bash -c "$LIM -q ctu list --name-includes IoT -a --malware-includes muhstik -f csv"
    assert_success
    assert_output '"Infection_Date","Capture_Name","Malware","MD5","SHA256","Capture_URL","ZIP","LABELED","BINETFLOW","PCAP","WEBLOGNG"
"2018-05-19","CTU-IoT-Malware-Capture-3-1","Muhstik","b8849fe97e39ae3afd6def618568bb09","5ce13670bc875e913e6f087a4ac0a9e343347d5babb3b5c63e1d1b199371f69a","https://mcfp.felk.cvut.cz/publicDatasets/IoTDatasets/CTU-IoT-Malware-Capture-3-1","fce7b8bbd1c1fba1d75b9dc1a60b25f49f68c9ec16b3656b52ed28290fc93c72.zip","","2018-05-21_capture.binetflow","2018-05-21_capture.pcap","2018-05-21_capture.weblogng"'
}

####  ctu get  ####

@test "\"lim -q --data-dir $BATS_RUN_TMPDIR ctu get botnet-254-1 --no-subdir pcap\" works" {
    [[ "$NETWORKING" == "UP" ]] || skip "Networking appears to be down"
    run bash -c "$LIM -q --data-dir $BATS_RUN_TMPDIR ctu get botnet-254-1 --no-subdir pcap"
    [ -f $BATS_RUN_TMPDIR/capture_win13.pcap ]
}

@test "\"lim -q ctu get Botnet-252-1 pcap --no-subdir \" gets PCAP file to cwd" {
    [[ "$NETWORKING" == "UP" ]] || skip "Networking appears to be down"
    run bash -c "(cd $BATS_RUN_TMPDIR && $LIM -q ctu get Botnet-252-1 pcap --no-subdir)"
    [ -f $BATS_RUN_TMPDIR/2017-05-14_win10.pcap ]
}

@test "\"lim -q ctu get Botnet-252-1 pcap\" gets PCAP file in subdir" {
    [[ "$NETWORKING" == "UP" ]] || skip "Networking appears to be down"
    run bash -c "(cd $BATS_RUN_TMPDIR && $LIM -q ctu get Botnet-252-1 pcap)"
    [ -d $BATS_RUN_TMPDIR/CTU-Malware-Capture-Botnet-252-1 ]
    [ -f $BATS_RUN_TMPDIR/CTU-Malware-Capture-Botnet-252-1/2017-05-14_win10.pcap ]
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

@test "\"lim -q ctu stats sha256\" works" {
    run bash -c "$LIM -q ctu stats sha256 2>/dev/null | head -n 3"
    assert_output '+------------------------------------------------------------------+-------+
| SHA256                                                           | Count |
+------------------------------------------------------------------+-------+'
}

# vim: set ts=4 sw=4 tw=0 et :
