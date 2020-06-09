load test_helper

# See definition of LIM in test_helpers.bash for why "main" is used
# in tests.

setup() {
    true
}

teardown() {
    rm -f CTU-Malware-Capture-Botnet-48/botnet-capture-20110816-sogou.ips
    rm -f CTU-Malware-Capture-Botnet-48/botnet-capture-20110816-sogou-time-shifted.pcap
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

@test "\"lim -q ctu get Botnet-48 pcap --no-subdir \" gets PCAP file to cwd" {
    run bash -c "[ -f botnet-capture-20110816-sogou.pcap ] || $LIM -q ctu get Botnet-48 pcap --no-subdir"
    [ -f botnet-capture-20110816-sogou.pcap ]
}

@test "\"lim -q ctu get Botnet-48 pcap\" gets PCAP file" {
    run bash -c "[ -f CTU-Malware-Capture-Botnet-48/botnet-capture-20110816-sogou.pcap ] || $LIM -q ctu get Botnet-48 pcap"
    [ -d CTU-Malware-Capture-Botnet-48 ]
    [ -f CTU-Malware-Capture-Botnet-48/botnet-capture-20110816-sogou.pcap ]
}

# vim: set ts=4 sw=4 tw=0 et :
