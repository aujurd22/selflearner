#!/bin/bash
# sweep all OpenRSI discussions' latest dispatcher review status
gh api graphql -f query='{
  repository(owner: "OpenRSI-Foundation", name: "OpenRSI-Index") {
    discussions(first: 50, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes {
        number
        title
        comments(last: 5) {
          nodes { body }
        }
      }
    }
  }
}' --jq '.data.repository.discussions.nodes[] |
  . as $d |
  ($d.comments.nodes | map(.body) | join(" ")) as $all |
  if ($all | test("rubric-review-status:completed")) then
    "#\($d.number) COMPLETED \($d.title[:60])"
  elif ($all | test("rubric-review-status:rejected")) then
    "#\($d.number) REJECTED \($d.title[:60])"
  elif ($all | test("rubric-review-status:failed")) then
    "#\($d.number) FAILED \($d.title[:60])"
  else empty end
' 2>&1 | grep -v "^w s l" | sort | uniq -c | sort -rn | head -60
