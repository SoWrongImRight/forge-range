alias ll="ls -la"
alias fw="curl http://forge-web:8080"
alias fi="curl http://forge-internal:5000"
alias fdb="psql -h forge-db -U app -d appdb"

export TARGET_WEB=forge-web
export TARGET_INTERNAL=forge-internal
export TARGET_DB=forge-db
export TARGET_SSH=forge-privesc
