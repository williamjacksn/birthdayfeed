install --mode=600 -D /dev/null ~/.ssh/id_ed25519
echo "${SSH_PRIVATE_KEY}" > ~/.ssh/id_ed25519
ssh-keyscan -H -p 53185 ${SSH_HOST} > ~/.ssh/known_hosts
ssh ssh://${SSH_USER}@${SSH_HOST}:53185 /usr/bin/docker compose --file /home/${SSH_USER}/syncthing/coruscant/compose.yaml pull birthdayfeed
ssh ssh://${SSH_USER}@${SSH_HOST}:53185 /usr/bin/docker compose --file /home/${SSH_USER}/syncthing/coruscant/compose.yaml up --detach birthdayfeed
ssh ssh://${SSH_USER}@${SSH_HOST}:53185 /usr/bin/docker image prune --force
