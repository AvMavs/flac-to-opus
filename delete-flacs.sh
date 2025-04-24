sudo find . -type f -name '*.flac' -print0 \
  | while IFS= read -r -d '' flac; do
      opus="${flac%.flac}.opus"
      if [ -f "$opus" ]; then
        echo "Deleting $flac (found $opus)"
        sudo rm -- "$flac"
      fi
    done
