#!/usr/bin/env bash
set -euo pipefail
cat >change.diff <<'DIFF'
diff --git a/client/http.go b/client/http.go
--- a/client/http.go
+++ b/client/http.go
@@ -12,10 +12,28 @@ type Client struct {
 	base string
 	hc   *http.Client
+	maxRetries int
 }

-func (c *Client) Get(ctx context.Context, path string) (*http.Response, error) {
-	return c.hc.Get(c.base + path)
+// Get retries 502, 503, and 504 with exponential backoff, because the
+// upstream gateway drops requests during deploys.
+func (c *Client) Get(ctx context.Context, path string) (*http.Response, error) {
+	var resp *http.Response
+	var err error
+	for attempt := 0; attempt <= c.maxRetries; attempt++ {
+		req, _ := http.NewRequestWithContext(ctx, http.MethodGet, c.base+path, nil)
+		resp, err = c.hc.Do(req)
+		if err == nil && resp.StatusCode < 502 {
+			return resp, nil
+		}
+		select {
+		case <-ctx.Done():
+			return nil, ctx.Err()
+		case <-time.After(time.Duration(1<<attempt) * 100 * time.Millisecond):
+		}
+	}
+	return resp, err
 }
diff --git a/client/http_test.go b/client/http_test.go
--- a/client/http_test.go
+++ b/client/http_test.go
@@ -40,3 +40,21 @@
+func TestGetRetriesGatewayErrors(t *testing.T) {
+	calls := 0
+	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
+		calls++
+		if calls < 3 {
+			w.WriteHeader(http.StatusBadGateway)
+			return
+		}
+		w.WriteHeader(http.StatusOK)
+	}))
+	defer srv.Close()
+	c := &Client{base: srv.URL, hc: srv.Client(), maxRetries: 3}
+	resp, err := c.Get(context.Background(), "/")
+	if err != nil || resp.StatusCode != 200 || calls != 3 {
+		t.Fatalf("got status %v, err %v, calls %d", resp, err, calls)
+	}
+}
DIFF
