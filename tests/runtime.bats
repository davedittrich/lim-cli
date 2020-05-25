load test_helper

# See definition of LIM in test_helpers.bash for why "main" is used
# in tests.

setup() {
    export VOL_PREFIX=$HOME/packet_cafe_data
    export PACKET_CAFE_STATUS=$(cat /tmp/packet_cafe_status 2>/dev/null || echo DOWN)
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

@test "\"lim pcap extract ips CTU-Malware-Capture-Botnet-48/botnet-capture-20110816-sogou.pcap\" works" {
    run bash -c "$LIM pcap extract ips CTU-Malware-Capture-Botnet-48/botnet-capture-20110816-sogou.pcap"
    [ -f CTU-Malware-Capture-Botnet-48/botnet-capture-20110816-sogou.ips ]
    run bash -c "cat CTU-Malware-Capture-Botnet-48/botnet-capture-20110816-sogou.ips"
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

@test "\"lim pcap extract ips --stdout CTU-Malware-Capture-Botnet-48/botnet-capture-20110816-sogou.pcap\" works" {
    run bash -c "$LIM pcap extract ips --stdout CTU-Malware-Capture-Botnet-48/botnet-capture-20110816-sogou.pcap"
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

@test "\"lim pcap shift time CTU-Malware-Capture-Botnet-48/botnet-capture-20110816-sogou.pcap --start-time 2019-01-01T12:00:01.0+0100\" works" {
    run bash -c "$LIM pcap shift time CTU-Malware-Capture-Botnet-48/botnet-capture-20110816-sogou.pcap --start-time 2019-01-01T12:00:01.0+0100"
    [ -f CTU-Malware-Capture-Botnet-48/botnet-capture-20110816-sogou-time-shifted.pcap ]
    run bash -c "tcpdump -c3 -nntttt -r CTU-Malware-Capture-Botnet-48/botnet-capture-20110816-sogou-time-shifted.pcap"
    assert_output "reading from file CTU-Malware-Capture-Botnet-48/botnet-capture-20110816-sogou-time-shifted.pcap, link-type EN10MB (Ethernet)
2019-01-01 04:00:01.000000 IP 147.32.84.165.1025 > 147.32.80.9.53: 328+ A? ping.ie.sogou.com. (35)
2019-01-01 04:00:01.000009 IP 147.32.84.165.1025 > 147.32.80.9.53: 328+ A? ping.ie.sogou.com. (35)
2019-01-01 04:00:01.000502 IP 147.32.80.9.53 > 147.32.84.165.1025: 328 3/3/0 CNAME config.ie.sogou.com., A 61.135.188.210, A 61.135.188.212 (147)"
}

@test "packet-cafe Docker containers are running" {
    bash -c "([ $(docker ps | grep cyberreboot | grep healthy | wc -l) -ge 7 ] && echo UP || echo DOWN) | tee /tmp/packet_cafe_status"
    [ -f /tmp/packet_cafe_status ]
    [ "$(cat /tmp/packet_cafe_status)" == "UP" ]
}

@test "\"lim cafe admin endpoints\" includes \"/v1/info\"" {
    [ "$PACKET_CAFE_STATUS" == "DOWN" ] && skip "packet-cafe not running"
    run bash -c "$LIM cafe admin endpoints"
    assert_output --partial "/v1/info"
}

@test "\"lim cafe tools\" includes \"cyberreboot/\"" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe tools"
    assert_output --partial "cyberreboot/"
}

@test "\"lim cafe info\" includes \"hostname\"" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe info"
    assert_output --partial "hostname"
}

@test "\"lim cafe admin info\" includes \"hostname\"" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe admin info"
    assert_output --partial "hostname"
}

@test "\"lim cafe admin sessions\" has no sessions" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe admin sessions"
    assert_output --partial "[-] packet-cafe server has no sessions"
}

@test "\"lim cafe upload ~/git/packet_cafe/notebooks/smallFlows.pcap\" works" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    [ -f $HOME/git/packet_cafe/notebooks/smallFlows.pcap ] || skip "No packet-cafe smallFlows.pcap available"
    run bash -c "$LIM cafe upload $HOME/git/packet_cafe/notebooks/smallFlows.pcap --session-id 00000000-9999-8888-7777-666666666666"
    assert_output --partial "[+] Upload smallFlows.pcap: success"
}

@test "\"lim cafe admin results\" contains \"metadata.json\" files" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe admin results -f value | grep 00000000-9999-8888-7777-666666666666"
    assert_output --partial "metadata.json"
}

@test "\"lim cafe admin files\" contains \"smallFlows.pcap\"" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe admin files -f value | grep 00000000-9999-8888-7777-666666666666"
    assert_output --partial "smallFlows.pcap"
}

@test "\"lim cafe upload CTU-Malware-Capture-Botnet-48/botnet-capture-20110816-sogou.pcap\" works" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe upload --session-id 11111111-2222-3333-4444-555555555555 CTU-Malware-Capture-Botnet-48/botnet-capture-20110816-sogou.pcap"
    assert_output --partial "[+] Upload botnet-capture-20110816-sogou.pcap: success"
}

@test "\"lim cafe admin sessions -f value\" shows both sessions" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe admin sessions -f value | sort"
    assert_output "00000000-9999-8888-7777-666666666666
11111111-2222-3333-4444-555555555555"
}

# TODO(dittrich): Fix syntax error
# @test "All tools produce results" {
#     bash -c "(for tool in $(lim cafe tools -c Name -f value); do lim -q cafe results --tool $tool 11111111-2222-3333-4444-555555555555 2>/dev/null; done) | grep Viewer | sort | uniq"
#     assert_output "  <title>Results Viewer</title>"
# }

@test "\"lim cafe admin delete --all\" leaves storage directory empty" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe admin delete --all"
    run bash -c "(cd $VOL_PREFIX && tree .)"
    assert_output ".
├── definitions
│   └── workers.json
├── files
├── id
└── redis
    └── appendonly.aof

4 directories, 2 files"
}

@test "Cleaning up /tmp/packet_cafe_status" {
    rm -f /tmp/packet_cafe_status
}

# vim: set ts=4 sw=4 tw=0 et :
