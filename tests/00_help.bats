load test_helper

# See definition of LIM in test_helpers.bash for why "main" is used
# in tests.

setup() {
    true
}

teardown() {
    true
}

@test "\"lim about\" contains \"version\"" {
    run bash -c "$LIM about"
    assert_output --partial 'version'
}

@test "'lim help' can load all entry points" {
    run $LIM help 2>&1
    refute_output --partial "Could not load EntryPoint"
}

@test "\"lim cafe --help\" properly lists subcommands" {
    run bash -c "$LIM cafe --help"
    assert_output 'Command "cafe" matches:
  cafe about
  cafe admin endpoints
  cafe admin files
  cafe admin info
  cafe admin results
  cafe admin sessions
  cafe endpoints
  cafe info
  cafe raw
  cafe requests
  cafe results
  cafe status
  cafe stop
  cafe tools
  cafe ui
  cafe upload'
}

@test "\"lim ctu --help\" properly lists subcommands" {
    run bash -c "$LIM ctu --help"
    assert_output 'Command "ctu" matches:
  ctu get
  ctu list
  ctu overview
  ctu stats'
}

@test "\"lim pcap --help\" properly lists subcommands" {
    run bash -c "$LIM pcap --help"
    assert_output 'Command "pcap" matches:
  pcap extract ips
  pcap shift network
  pcap shift time'
}

@test "'lim --version' works" {
    run $LIM --version
    assert_output --partial "main"
}

# vim: set ts=4 sw=4 tw=0 et :
