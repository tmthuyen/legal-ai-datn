package hash

import "testing"

var pkg = "[HASH]"

// [Test Hash] Func: Hash & Verify Password
func TestHashPassword(t *testing.T) {
	pass := "12345678"

	hashed, err := Password(pass)

	if err != nil {
		t.Errorf("%s Hash password thất bại: %v", pkg, err)
	}

	err = Verify(hashed, pass)

	if err != nil {
		t.Errorf("%s Verify password thất bại: %v", pkg, err)
	}

	t.Logf("%s Test hash password success", pkg)
}
