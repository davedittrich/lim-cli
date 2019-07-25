load test_helper

# See definition of LIM in test_helpers.bash for why "main" is used
# in tests.

setup() {
    true
}

teardown() {
    true
}

@test "'lim help' can load all entry points" {
    run $LIM help 2>&1
    refute_output --partial "Could not load EntryPoint"
}

@test "'lim --version' works" {
    run $LIM --version
    assert_output --partial "main"
}

# vim: set ts=4 sw=4 tw=0 et :
