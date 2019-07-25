load test_helper

# See definition of LIM in test_helpers.bash for why "main" is used
# in tests.

setup() {
}

teardown() {
}

@test "'lim about' contains 'version'" {
    run bash -c "$LIM -q about"
    assert_output --partial 'version'
}

# vim: set ts=4 sw=4 tw=0 et :
