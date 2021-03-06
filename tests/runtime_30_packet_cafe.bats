#!/usr/bin/env bats

load test_helper

# See definition of LIM in test_helpers.bash for why "main" is used
# in tests.

setup_file() {
    if [[ -z "$VOL_PREFIX" ]]; then
        echo 'Environment variable "VOL_PREFIX" is not set' >&2
        return 1
    fi
    if ! $LIM -q cafe docker ps; then
        echo "Packet Cafe containers are not running ('lim cafe docker up'?)" >&2
        return 1
    fi
    if $LIM -q cafe admin sessions; then
        echo "Packet Cafe has existing sessions ('lim cafe admin delete --all'?)" >&2
        return 1
    fi
    # Make sure needed PCAP file is present (don't rely on earlier tests)
    if [[ ! -f 2015-04-09_capture-win2.pcap ]]; then
        $LIM -q ctu get Botnet-114-1 pcap --no-subdir
    fi
    eval "grep NO_SESSIONS_MSG lim/packet_cafe/__init__.py"
    export NO_SESSIONS_MSG
}

setup() {
    true
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
# cafe docker build      No
# cafe docker down       No
# cafe docker images     Yes
# cafe docker pull       No
# cafe docker ps         Yes
# cafe docker up         No
# cafe endpoints         Yes
# cafe info              Yes
# cafe raw               Yes
# cafe report            Yes
# cafe requests          Yes
# cafe results           Yes
# cafe status            Yes
# cafe stop              Yes (for no sessions: API call not implemented yet)
# cafe tools             Yes
# cafe ui                Yes
# cafe upload            Yes

@test "\"lim cafe docker up\" fails" {
    run bash -c "$LIM cafe docker up"
    assert_failure
    assert_output "[-] packet-cafe containers are already running"
}

@test "\"lim cafe docker images\" succeeds" {
    run bash -c "$LIM cafe docker images"
    assert_success
    assert_output --partial '[+] listing images for service namespace "iqtlabs", tool namespace "iqtlabs"'
    assert_output --partial 'Repository'
    assert_output --partial 'packet_cafe_admin'
}

@test "\"lim -q cafe docker ps\" succeeds w/o output" {
    run bash -c "$LIM -q cafe docker ps"
    assert_success
    assert_output ""
}

@test "\"lim cafe docker ps\" succeeds w/ output" {
    run bash -c "$LIM cafe docker ps"
    assert_success
    assert_output --partial "short_id"
    assert_output --partial "packet_cafe_admin_"
}

@test "\"lim cafe endpoints\" includes \"/api/v1/info\"" {
    run bash -c "$LIM cafe endpoints"
    assert_success
    assert_output --partial "/api/v1/info"
}

@test "\"lim cafe admin endpoints\" includes \"/v1/info\"" {
    run bash -c "$LIM cafe admin endpoints"
    assert_success
    assert_output --partial "/v1/info"
}

@test "\"lim cafe about\" fails (no tty)" {
    run bash -c "$LIM cafe about < /dev/null"
    assert_failure
    assert_output --partial "[-] use --force to open browser when stdin is not a TTY"
}

@test "\"lim cafe ui\" fails (no tty)" {
    run bash -c "$LIM cafe ui < /dev/null"
    assert_failure
    assert_output --partial "[-] use --force to open browser when stdin is not a TTY"
}

@test "\"lim cafe tools\" includes \"iqtlabs/\"" {
    run bash -c "$LIM cafe tools"
    assert_success
    assert_output --partial "iqtlabs/"
}

@test "\"lim cafe info\" includes \"hostname\"" {
    run bash -c "$LIM cafe info"
    assert_success
    assert_output --partial "hostname"
}

@test "\"lim cafe admin info\" includes \"hostname\"" {
    run bash -c "$LIM cafe admin info"
    assert_success
    assert_output --partial "hostname"
}

@test "\"lim cafe info\" shows last_session_id == None" {
    run bash -c "$LIM cafe info -f shell | grep last_session"
    assert_success
    assert_output 'last_session_id="None"'
}

@test "\"lim cafe admin sessions\" fails with messsage" {
    run bash -c "$LIM cafe admin sessions"
    assert_failure
    assert_output '[-] packet-cafe server has no sessions'
}

@test "\"lim -q cafe admin sessions\" fails with no output" {
    run bash -c "$LIM -q cafe admin sessions"
    assert_failure
    assert_output ''
}

@test "\"lim cafe upload --wait ~/git/packet_cafe/notebooks/smallFlows_nopayloads.pcap\" works" {
    [ -f $HOME/git/packet_cafe/notebooks/smallFlows_nopayloads.pcap ] || skip "No packet-cafe smallFlows_nopayloads.pcap available"
    run bash -c "$LIM cafe upload --wait $HOME/git/packet_cafe/notebooks/smallFlows_nopayloads.pcap 11111111-1111-1111-1111-111111111111"
    assert_success
    assert_output --partial "[+] Upload smallFlows_nopayloads.pcap: success"
}

@test "The last upload created last session/request state" {
    [ -f ${VOL_PREFIX}/files/last_session_id ]
    [ -f ${VOL_PREFIX}/files/last_request_id ]
}

@test "\"lim cafe info\" shows last_session_id == 11111111-1111-1111-1111-111111111111" {
    run bash -c "$LIM cafe info -f shell | grep last_session"
    assert_success
    assert_output 'last_session_id="11111111-1111-1111-1111-111111111111"'
}

@test "\"lim -q cafe admin sessions\" returns success" {
    run bash -c "$LIM -q cafe admin sessions"
    assert_success
}

@test "\"lim cafe status\" contains \"Complete\"" {
    run bash -c "$LIM cafe status -f value"
    assert_success
    assert_output --partial "Complete"
}

@test "\"lim cafe admin results\" contains \"metadata.json\" files" {
    run bash -c "$LIM cafe admin results -f value | grep 11111111-1111-1111-1111-111111111111"
    assert_success
    assert_output --partial "metadata.json"
}

@test "\"lim cafe admin files\" contains \"smallFlows_nopayloads.pcap\"" {
    run bash -c "$LIM cafe admin files -f value | grep 11111111-1111-1111-1111-111111111111"
    assert_success
    assert_output --partial "smallFlows_nopayloads.pcap"
}

@test "\"lim cafe upload --wait 2015-04-09_capture-win2.pcap\" works" {
    run bash -c "$LIM cafe upload --wait 2015-04-09_capture-win2.pcap 22222222-2222-2222-2222-222222222222"
    assert_success
    assert_output --partial "[+] Upload 2015-04-09_capture-win2.pcap: success"
}

@test "\"lim -q cafe requests\" includes \"2015-04-09_capture-win2.pcap\"" {
    run bash -c "$LIM -q cafe requests -f value"
    assert_success
    assert_output --partial "2015-04-09_capture-win2.pcap"
}

@test "\"lim -q cafe report --tool poof\" fails" {
    run bash -c "$LIM -q cafe report --tool poof"
    assert_failure
    assert_output --partial "[-] no reportable output for tool 'poof'"
}

@test "\"lim -q cafe report --tool p0f\" works" {
    run bash -c "$LIM -q cafe report --tool p0f | md5sum -"
    assert_output --partial "49b5e331b4827878786796e285b9217e"
}

@test "\"lim cafe results --tool networkml\" works" {
    run bash -c "$LIM cafe raw --tool networkml"
    assert_success
    assert_output --partial ' "decisions": {'
}

@test "\"lim cafe admin sessions -f value\" shows both sessions" {
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
    run bash -c "$LIM cafe admin delete --all"
    assert_success
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

@test "\"lim cafe admin delete --all\" fails when repeated" {
    run bash -c "$LIM cafe admin delete --all"
    assert_failure
    assert_output --partial "$NO_SESSIONS_MSG"
}

@test "\"lim cafe info\" shows last_session_id == None (repeat)" {
    run bash -c "$LIM cafe info -f shell | grep last_session"
    assert_output 'last_session_id="None"'
}

@test "\"lim cafe admin sessions\" fails with msg (repeat)" {
    run bash -c "$LIM cafe admin sessions"
    assert_failure
    assert_output --partial "$NO_SESSIONS_MSG"
}

@test "\"lim cafe report --tool p0f\" fails (no sessions)" {
    run bash -c "$LIM cafe report --tool p0f"
    assert_failure
    assert_output --partial "$NO_SESSIONS_MSG"
}

@test "\"lim cafe results\" fails with message" {
    run bash -c "$LIM cafe results"
    assert_failure
    assert_output --partial "$NO_SESSIONS_MSG"
}

@test "\"lim cafe raw --tool p0f\" fails (no sessions)" {
    run bash -c "$LIM cafe raw --tool p0f"
    assert_failure
    assert_output --partial "$NO_SESSIONS_MSG"
}

@test "\"lim cafe stop\" fails with message" {
    run bash -c "$LIM cafe stop"
    assert_failure
    assert_output --partial "$NO_SESSIONS_MSG"
}

@test "\"lim cafe requests\" fails with message" {
    run bash -c "$LIM cafe requests"
    assert_failure
    assert_output --partial "$NO_SESSIONS_MSG"
}

@test "\"lim cafe status\" fails with message" {
    run bash -c "$LIM cafe status"
    assert_failure
    assert_output --partial "$NO_SESSIONS_MSG"
}

# vim: set ts=4 sw=4 tw=0 et :
