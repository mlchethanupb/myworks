#!/bin/bash
# K8 for Ubuntu 18.04

# Example
# ./install-k8.sh --metallb-config metallb-config.yaml --dashboard enable --docker-remote-api enable --network-adapter ens33

install_k8s() {
    USERNAME=$(id -nu)

    # argument parsing
    POSITIONAL=()
    while [[ $# -gt 0 ]]
    do
    key="$1"

    case $key in
        -m|--metallb-config)
        METALLB_CONF="$2"
        shift
        shift
        ;;
        -d|--dashboard)
        DASHBOARD="$2"
        shift
        shift
        ;;
        -r|--docker-remote-api)
        DOCKER_REMOTE_API="$2"
        shift
        shift
        ;;
        -n|--network-adapter)
        NETWORK_ADAPTER="$2"
        shift
        shift
        ;;
        *)
        POSITIONAL+=("$1")
        shift
        ;;
    esac
    done
    set -- "${POSITIONAL[@]}" # restore positional parameters

    # set default values if not set
    if [ -z "${METALLB_CONF}" ]
      then
        METALLB_CONF='metallb-config.yaml'
    fi

    if [ -z "${DASHBOARD}" ]
      then
        DASHBOARD='disable'
    fi

    if [ -z "${DOCKER_REMOTE_API}" ]
      then
        DOCKER_REMOTE_API='disable'
    fi

    if [ -z "${NETWORK_ADAPTER}" ]
      then
        printf "${RED}Error: Need to specifiy network adapter\nExample: --network-adapter eth0${NC}\n"
        exit 1
      else
        IP_ADDRESS=$(ip address show ${NETWORK_ADAPTER} | grep -Po 'inet \K[\d.]+')
    fi

    ORANGE='\033[0;33m'
    RED='\033[0;31m'
    NC='\033[0m'
    #echo 'user ALL=(ALL:ALL) ALL' | sudo EDITOR='tee -a' visudo

    printf "${ORANGE}[Installing prerequisites]${NC}\n"
    sudo apt-get update && sudo apt-get install -y apt-transport-https curl gnupg2 docker.io
    sudo systemctl enable docker.service
    sudo swapoff -a

    if [ "${DOCKER_REMOTE_API}" = 'enable' ] ; then
        printf "${ORANGE}[Enabling Docker Remote API]${NC}\n"
        sudo mkdir -p /etc/systemd/system/docker.service.d/
        printf "[Service]\nExecStart=\nExecStart=/usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock -H tcp://0.0.0.0:1111\n" | sudo tee /etc/systemd/system/docker.service.d/override.conf
        sudo systemctl daemon-reload
        sudo systemctl restart docker.service
    fi

    printf "${ORANGE}[Installing Kubernetes]${NC}\n"
    curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
    echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list
    sudo apt-get update
    sudo apt-get install -y kubelet=1.14.8-00 kubeadm=1.14.8-00 kubectl=1.14.8-00
    sudo apt-mark hold kubelet kubeadm kubectl
    sudo kubeadm init

    printf "${ORANGE}[Making kubectl available to \'${USERNAME}\']${NC}\n"
    mkdir -p $HOME/.kube
    sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
    sudo chown $(id -u):$(id -g) $HOME/.kube/config

    if [ "${DASHBOARD}" = 'enable' ] ; then
        printf "${ORANGE}[Starting Dashboard]${NC}\n"
        kubectl create -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.0-beta4/aio/deploy/recommended.yaml
        nohup kubectl proxy --address=0.0.0.0 --port=8001 > /dev/null 2>&1 < /dev/null &
    fi

    printf "${ORANGE}[Installing Weave Net]${NC}\n"
    kubectl create clusterrolebinding dashboard-default-user --clusterrole=cluster-admin --user=system:serviceaccount:default:default
    kubectl create clusterrolebinding dashboard-default-weave-net --clusterrole=cluster-admin --user=system:serviceaccount:kube-system:weave-net
    sudo sysctl net.bridge.bridge-nf-call-iptables=1
    kubectl apply -f "https://cloud.weave.works/k8s/net?k8s-version=$(kubectl version | base64 | tr -d '\n')"
    # kubectl get pods -n kube-system -o wide

    printf "${ORANGE}[Installing MetalLB]${NC}\n"
    kubectl apply -f https://raw.githubusercontent.com/google/metallb/v0.7.3/manifests/metallb.yaml
    kubectl apply -f ${METALLB_CONF}
    # kubectl get pods -n kube-system -l name=weave-net

    printf "${ORANGE}[Untainting master node]${NC}\n"
    kubectl taint nodes --all node-role.kubernetes.io/master-


    if [ "${DASHBOARD}" = 'enable' ] ; then
        printf "${ORANGE}[To enable Dashboard Access run: ssh -L localhost:8001:${IP_ADDRESS}:8001 ${USERNAME}@${IP_ADDRESS} -N]${NC}\n"
        printf "${ORANGE}[Access Dashboard: http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/]${NC}\n"
    fi
}

test() {
    echo 'success'
    USERNAME=$(id -nu)

    # argument parsing
    POSITIONAL=()
    while [[ $# -gt 0 ]]
    do
    key="$1"

    case $key in
        -m|--metallb-config)
        METALLB_CONF="$2"
        shift
        shift
        ;;
        -d|--dashboard)
        DASHBOARD="$2"
        shift
        shift
        ;;
        -r|--docker-remote-api)
        DOCKER_REMOTE_API="$2"
        shift
        shift
        ;;
        -n|--network-adapter)
        NETWORK_ADAPTER="$2"
        shift
        shift
        ;;
        *)
        POSITIONAL+=("$1")
        shift
        ;;
    esac
    done
    set -- "${POSITIONAL[@]}" # restore positional parameters
    echo $NETWORK_ADAPTER
}

if [[ "$OSTYPE" == "linux-gnu" ]]; then
    if [[ $(awk -F= '/^NAME/{print $2}' /etc/os-release) == '"Ubuntu"' ]]; then
        if [[ $(lsb_release -rs) == "18.04" ]]; then
               echo "Compatible OS detected"
               install_k8s $@
        fi
    fi
else
   echo "Non-compatible OS or OS version detected"
fi

# UNINSTALL K8
# kubectl drain <node name> --delete-local-data --force --ignore-daemonsets
# kubectl delete node <node name>

# sudo kubeadm reset

# debian-based
# sudo apt-get purge kubeadm kubectl kubelet kubernetes-cni kube* 
# sudo apt-get autoremove

# centos-based
# sudo yum remove kubeadm kubectl kubelet kubernetes-cni kube*
# sudo yum autoremove
 
# sudo rm -rf ~/.kube
