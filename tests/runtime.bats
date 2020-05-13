load test_helper

# See definition of LIM in test_helpers.bash for why "main" is used
# in tests.

setup() {
    true
    export SCENARIO="CTU-Malware-Capture-Botnet-48"
}

teardown() {
    rm -f $SCENARIO/botnet-capture-20110816-sogou.ips
    rm -f $SCENARIO/botnet-capture-20110816-sogou-time-shifted.pcap
}

@test "\"lim about\" contains \"version\"" {
    run bash -c "$LIM -q about"
    assert_output --partial 'version'
}

@test "\"lim -q ctu list $SCENARIO\" works" {
    run bash -c "$LIM -q ctu list $SCENARIO"
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

@test "\"lim -q ctu get Botnet-48 pcap\" gets PCAP file" {
    run bash -c "[ -f $SCENARIO/botnet-capture-20110816-sogou.pcap ] || $LIM -q ctu get Botnet-48 pcap"
    [ -d $SCENARIO ]
    [ -f $SCENARIO/botnet-capture-20110816-sogou.pcap ]
}

@test "\"lim pcap extract ips $SCENARIO/botnet-capture-20110816-sogou.pcap\" works" {
    run bash -c "$LIM pcap extract ips $SCENARIO/botnet-capture-20110816-sogou.pcap"
    [ -f $SCENARIO/botnet-capture-20110816-sogou.ips ]
    run bash -c "cat $SCENARIO/botnet-capture-20110816-sogou.ips"
    assert_output '61.135.188.157
61.135.188.210
61.135.188.212
61.135.189.50
118.228.148.32
123.126.51.33
123.126.51.57
123.126.51.64
123.126.51.65
147.32.80.9
147.32.84.79
147.32.84.165
147.32.84.255
195.113.232.73
209.85.149.160
218.29.42.137
220.181.69.213
220.181.111.147'
}

@test "\"lim pcap extract ips --stdout $SCENARIO/botnet-capture-20110816-sogou.pcap\" works" {
    run bash -c "$LIM pcap extract ips --stdout $SCENARIO/botnet-capture-20110816-sogou.pcap"
    assert_output '61.135.188.157
61.135.188.210
61.135.188.212
61.135.189.50
118.228.148.32
123.126.51.33
123.126.51.57
123.126.51.64
123.126.51.65
147.32.80.9
147.32.84.79
147.32.84.165
147.32.84.255
195.113.232.73
209.85.149.160
218.29.42.137
220.181.69.213
220.181.111.147'
}

@test "\"lim pcap shift time $SCENARIO/botnet-capture-20110816-sogou.pcap --start-time 2019-01-01T12:00:01.0+0100\" works" {
    run bash -c "$LIM pcap shift time $SCENARIO/botnet-capture-20110816-sogou.pcap --start-time 2019-01-01T12:00:01.0+0100"
    [ -f $SCENARIO/botnet-capture-20110816-sogou-time-shifted.pcap ]
    run bash -c "tcpdump -c3 -nntttt -r $SCENARIO/botnet-capture-20110816-sogou-time-shifted.pcap"
    assert_output "reading from file $SCENARIO/botnet-capture-20110816-sogou-time-shifted.pcap, link-type EN10MB (Ethernet)
2019-01-01 04:00:01.000000 IP 147.32.84.165.1025 > 147.32.80.9.53: 328+ A? ping.ie.sogou.com. (35)
2019-01-01 04:00:01.000009 IP 147.32.84.165.1025 > 147.32.80.9.53: 328+ A? ping.ie.sogou.com. (35)
2019-01-01 04:00:01.000502 IP 147.32.80.9.53 > 147.32.84.165.1025: 328 3/3/0 CNAME config.ie.sogou.com., A 61.135.188.210, A 61.135.188.212 (147)"
}

# vim: set ts=4 sw=4 tw=0 et :
