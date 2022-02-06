#!/bin/sh
cd C:/Work/Presupuesto
git add --all
timestamp() {
  date +"at %H:%M:%S on %d/%m/%Y"
}
git commit -am "Regular auto-commit $(timestamp)"
git push origin develop:develop-backup