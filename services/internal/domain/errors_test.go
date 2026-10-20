package domain

import (
	"testing"
)

var pkg = "[INTERNAL DOMAIN]"

// [Test Error]Func: Error
func TestError(t *testing.T) {

	// bad err
	bad := ErrBadRequest("Bad Request", "Error 1", "Error 2")

	if bad.StatusCode != 400 {
		t.Errorf("%s Error request không đúng status code", pkg)
	}

	if bad.Message == "" || len(bad.Errors) == 0 {
		t.Errorf("%s Error request không hợp lệ", pkg)
	}

	// internal err
	internal := ErrInternal("Internal Server Error", "Error 1", "Error 2")

	if internal.StatusCode != 500 {
		t.Errorf("%s Error internal không đúng status code", pkg)
	}

	if internal.Message == "" || len(internal.Errors) == 0 {
		t.Errorf("%s Error internal không hợp lệ", pkg)
	}

	t.Logf("%s Test Error request invalid", pkg)
}
