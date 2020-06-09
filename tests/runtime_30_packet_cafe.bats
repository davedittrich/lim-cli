load test_helper

# See definition of LIM in test_helpers.bash for why "main" is used
# in tests.

setup() {
    export VOL_PREFIX=$HOME/packet_cafe_data
    export PACKET_CAFE_STATUS=$(cat /tmp/packet_cafe_status 2>/dev/null || echo DOWN)
}

teardown() {
    true
}

@test "packet-cafe Docker containers are running (via \"docker ps\")" {
    bash -c "([ $(docker ps | grep cyberreboot | grep healthy | wc -l) -ge 7 ] && echo UP || echo DOWN) | tee /tmp/packet_cafe_status"
    [ -f /tmp/packet_cafe_status ]
    [ "$(cat /tmp/packet_cafe_status)" == "UP" ]
}

@test "\"lim cafe containers --check-running\" reports Docker containers are running" {
    run bash -c "$LIM cafe containers --check-running"
    assert_success
}

@test "\"lim cafe endpoints\" includes \"/api/v1/info\"" {
    [ "$PACKET_CAFE_STATUS" == "DOWN" ] && skip "packet-cafe not running"
    run bash -c "$LIM cafe endpoints"
    assert_output --partial "/api/v1/info"
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

@test "\"lim cafe upload --wait ~/git/packet_cafe/notebooks/smallFlows.pcap\" works" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    [ -f $HOME/git/packet_cafe/notebooks/smallFlows.pcap ] || skip "No packet-cafe smallFlows.pcap available"
    run bash -c "$LIM cafe upload --wait $HOME/git/packet_cafe/notebooks/smallFlows.pcap 11111111-1111-1111-1111-111111111111"
    assert_output --partial "[+] Upload smallFlows.pcap: success"
}

@test "\"lim cafe admin results\" contains \"metadata.json\" files" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe admin results -f value | grep 11111111-1111-1111-1111-111111111111"
    assert_output --partial "metadata.json"
}

@test "\"lim cafe admin files\" contains \"smallFlows.pcap\"" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe admin files -f value | grep 11111111-1111-1111-1111-111111111111"
    assert_output --partial "smallFlows.pcap"
}

@test "\"lim cafe upload --wait CTU-Malware-Capture-Botnet-48/botnet-capture-20110816-sogou.pcap\" works" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe upload --wait CTU-Malware-Capture-Botnet-48/botnet-capture-20110816-sogou.pcap 22222222-2222-2222-2222-222222222222"
    assert_output --partial "[+] Upload botnet-capture-20110816-sogou.pcap: success"
}

@test "\"lim -q cafe report --tool p0f\" works" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM -q cafe report --tool p0f | md5sum -"
    assert_output --partial "045434a0acfbe01544ea62c610a42357"
}

@test "\"lim cafe results --tool networkml\" works" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe raw --tool networkml"
    assert_output --partial '"source_ip": "147.32.84.79"'
}

@test "\"lim cafe admin sessions -f value\" shows both sessions" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe admin sessions -f value | sort"
    assert_output "11111111-1111-1111-1111-111111111111
22222222-2222-2222-2222-222222222222"
}

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

@test "\"lim cafe raw --tool p0f\" fails" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe raw --tool p0f"
    assert_output --partial "[-] session ID not provided"
}

@test "\"lim cafe raw --tool p0f --choose\" fails" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe raw --tool p0f"
    assert_output --partial "[-] session ID not provided"
}

@test "\"lim cafe results --tool p0f\" fails" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe raw --tool p0f"
    assert_output --partial "[-] session ID not provided"
}

@test "\"lim cafe results --choose\" fails" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe results --choose"
    assert_output --partial "[-] no sessions available"
}

@test "Cleaning up /tmp/packet_cafe_status" {
    rm -f /tmp/packet_cafe_status
}

# vim: set ts=4 sw=4 tw=0 et :
