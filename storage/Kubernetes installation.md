Kubernetes master node setup:

pip install kubernetes

./install-k8s.sh \
  --metallb-config metallb-config.yaml \
  --dashboard enable \
  --docker-remote-api enable \
  --network-adapter ens33

#The above command is denied, to allow permission, following command is needed to run

chmod u=rx "./install-k8s.sh"

#And then run the install-k8.sh file with skip-phase using the following command

./install-k8s.sh --skip-phases=preflight\
  --metallb-config metallb-config.yaml \
  --dashboard enable \
  --docker-remote-api enable \
  --network-adapter ens33


kubeadm token create --print-join-command


For worker node setup:

pip install kubernetes

curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubelet=1.14.8-00 kubeadm=1.14.8-00 kubectl=1.14.8-00
sudo apt-mark hold kubelet kubeadm kubectl

kubeadm join --skip-phases=preflight 131.234.28.213:6443 --token kz47wv.u3w7fnx02m9aa2lj     --discovery-token-ca-cert-hash sha256:3ebfc83d5c4c641c9387ca948fc77349bbcd5d0b4ba918c4479409ac1505a7d




#join command doesn't work

sudo kubeadm init
sudo kubeadm reset
sudo kubeadm join --skip-phases=preflight  --token kz47wv.u3w7fnx02m9aa2lj  131.234.28.213:6443 --discovery-token-unsafe-skip-ca-verification


