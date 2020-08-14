load test_helper

# See definition of LIM in test_helpers.bash for why "main" is used
# in tests.

setup() {
    export PACKET_CAFE_STATUS=$(cat /tmp/packet_cafe_status 2>/dev/null || echo DOWN)
}

teardown() {
    true
}

# Command test coverage (i.e., one or more tests exist):
# cafe about             Yes
# cafe admin delete      Yes
# cafe admin endpoints   Yes
# cafe admin files       Yes
# cafe admin info        Yes
# cafe admin results     Yes
# cafe admin sessions    Yes
# cafe containers        Yes
# cafe endpoints         Yes
# cafe info              Yes
# cafe raw               Yes
# cafe report            Yes
# cafe requests          Yes
# cafe results           Yes
# cafe status            Yes
# cafe stop              No (API call not implemented yet)
# cafe tools             Yes
# cafe ui                Yes
# cafe upload            Yes

@test "VOL_PREFIX is exported" {
    [ ! -z "$VOL_PREFIX" ]
}

@test "packet-cafe Docker containers are running (via \"docker ps\")" {
    bash -c "([ $(docker ps --filter 'name=packet_cafe' | grep healthy | wc -l) -ge 7 ] && echo UP || echo DOWN) | tee /tmp/packet_cafe_status"
    [ -f /tmp/packet_cafe_status ]
    [ "$(cat /tmp/packet_cafe_status)" == "UP" ]
}

@test "\"lim -q cafe containers\" reports Docker containers are running" {
    run bash -c "$LIM -q cafe containers"
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

@test "\"lim cafe about\" fails (no tty)" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe about < /dev/null"
    assert_failure
    assert_output --partial "[-] use --force to open browser when stdin is not a TTY"
}

@test "\"lim cafe ui\" fails (no tty)" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe ui < /dev/null"
    assert_failure
    assert_output --partial "[-] use --force to open browser when stdin is not a TTY"
}

@test "\"lim cafe tools\" includes \"iqtlabs/\"" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe tools"
    assert_output --partial "iqtlabs/"
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

@test "\"lim cafe info\" shows last_session_id == None" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe info -f shell | grep last_session"
    assert_output 'last_session_id="None"'
}

@test "\"lim cafe admin sessions\" has no sessions" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe admin sessions"
    assert_output --partial "[-] packet-cafe server has no sessions"
}

@test "\"lim -q cafe admin sessions\" returns failure" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM -q cafe admin sessions"
    assert_failure
}

@test "\"lim cafe upload --wait ~/git/packet_cafe/notebooks/smallFlows_nopayloads.pcap\" works" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    [ -f $HOME/git/packet_cafe/notebooks/smallFlows_nopayloads.pcap ] || skip "No packet-cafe smallFlows_nopayloads.pcap available"
    run bash -c "$LIM cafe upload --wait $HOME/git/packet_cafe/notebooks/smallFlows_nopayloads.pcap 11111111-1111-1111-1111-111111111111"
    assert_output --partial "[+] Upload smallFlows_nopayloads.pcap: success"
}

@test "The last upload created last session/request state" {
    [ -f ${VOL_PREFIX}/files/last_session_id ]
    [ -f ${VOL_PREFIX}/files/last_request_id ]
}

@test "\"lim cafe info\" shows last_session_id == 11111111-1111-1111-1111-111111111111" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe info -f shell | grep last_session"
    assert_output 'last_session_id="11111111-1111-1111-1111-111111111111"'
}

@test "\"lim -q cafe admin sessions\" returns success" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM -q cafe admin sessions"
    assert_success
}

@test "\"lim cafe status\" contains \"Complete\"" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe status -f value"
    assert_output --partial "Complete"
}

@test "\"lim cafe admin results\" contains \"metadata.json\" files" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe admin results -f value | grep 11111111-1111-1111-1111-111111111111"
    assert_output --partial "metadata.json"
}

@test "\"lim cafe admin files\" contains \"smallFlows_nopayloads.pcap\"" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe admin files -f value | grep 11111111-1111-1111-1111-111111111111"
    assert_output --partial "smallFlows_nopayloads.pcap"
}

@test "\"lim cafe upload --wait CTU-Malware-Capture-Botnet-48/botnet-capture-20110816-sogou.pcap\" works" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe upload --wait CTU-Malware-Capture-Botnet-48/botnet-capture-20110816-sogou.pcap 22222222-2222-2222-2222-222222222222"
    assert_output --partial "[+] Upload botnet-capture-20110816-sogou.pcap: success"
}

@test "\"lim -q cafe report --tool poof\" fails" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM -q cafe report --tool poof"
    assert_failure
    assert_output --partial "[-] no reportable output for tool 'poof'"
}

@test "\"lim -q cafe report --tool p0f\" works" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM -q cafe report --tool p0f | md5sum -"
    assert_output --partial "045434a0acfbe01544ea62c610a42357"
}

@test "\"lim cafe results --tool networkml\" works" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe raw --tool networkml"
    assert_output --partial ' "decisions": {'
}

@test "\"lim cafe admin sessions -f value\" shows both sessions" {
    [ "$PACKET_CAFE_STATUS" == "UP" ] || skip "packet-cafe not running"
    run bash -c "$LIM cafe admin sessions -f value | sort"
    assert_output "11111111-1111-1111-1111-111111111111
22222222-2222-2222-2222-222222222222"
}

@test "\"lim cafe admin delete 22222222-2222-2222-2222-222222222222\" removes session/request state" {
    run bash -c "$LIM cafe admin delete 22222222-2222-2222-2222-222222222222"
    [ ! -f ${VOL_PREFIX}/files/last_session_id ]
    [ ! -f ${VOL_PREFIX}/files/last_request_id ]
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
    assert_failure
    assert_output --partial "[-] session ID not provided"
}

@test "Cleaning up /tmp/packet_cafe_status" {
    rm -f /tmp/packet_cafe_status
}

# vim: set ts=4 sw=4 tw=0 et :
