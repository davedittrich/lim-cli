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

@test "\"lim -q ctu list CTU-Malware-Capture-Botnet-48\" works" {
    run bash -c "$LIM -q ctu list CTU-Malware-Capture-Botnet-48"
    assert_output '+-----------+---------+---------------+-------------------------------------------------------------------------+
| SCENARIO  | GROUP   | PROBABLE_NAME | SCENARIO_URL                                                            |
+-----------+---------+---------------+-------------------------------------------------------------------------+
| Botnet-48 | malware | Sogou         | https://mcfp.felk.cvut.cz/publicDatasets/CTU-Malware-Capture-Botnet-48/ |
+-----------+---------+---------------+-------------------------------------------------------------------------+'
}

@test "\"lim -q ctu list Botnet-48\" works" {
    run bash -c "$LIM -q ctu list Botnet-48"
    assert_output '+-----------+---------+---------------+-------------------------------------------------------------------------+
| SCENARIO  | GROUP   | PROBABLE_NAME | SCENARIO_URL                                                            |
+-----------+---------+---------------+-------------------------------------------------------------------------+
| Botnet-48 | malware | Sogou         | https://mcfp.felk.cvut.cz/publicDatasets/CTU-Malware-Capture-Botnet-48/ |
+-----------+---------+---------------+-------------------------------------------------------------------------+'
}

@test "\"lim -q ctu get Botnet-114-1 pcap\" gets PCAP file in subdir" {
    run bash -c "[ -f CTU-Malware-Capture-Botnet-114-1/2015-04-09_capture-win2.pcap ] || $LIM -q ctu get Botnet-114-1 pcap"
    [ -d CTU-Malware-Capture-Botnet-114-1 ]
    [ -f CTU-Malware-Capture-Botnet-114-1/2015-04-09_capture-win2.pcap ]
}

@test "\"lim -q ctu get Botnet-114-1 pcap --no-subdir \" gets PCAP file to cwd" {
    run bash -c "[ -f 2015-04-09_capture-win2.pcap ] || $LIM -q ctu get Botnet-114-1 pcap --no-subdir"
    [ -f 2015-04-09_capture-win2.pcap ]
}

# vim: set ts=4 sw=4 tw=0 et :
