#!/bin/bash
# Records the compute node's hardware and load for env.json (brief Part 6.2).
set -u
OUT=/home/$USER/RAO_OCT/stage1/probe/probe_${1}.txt
{
echo "## date"; date -Is
echo "## host"; hostname
echo "## pbs"; echo "job=$PBS_JOBID queue=$PBS_QUEUE ncpus_assigned=${NCPUS:-?}"
echo "## lscpu"; lscpu
echo "## nproc (visible to job)"; nproc
echo "## memory"; free -g
echo "## frequency scaling"
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo "no cpufreq governor visible"
cat /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null && echo "(intel_pstate no_turbo above)"
echo "## other users' processes on this node"
ps -eo user= | sort | uniq -c | sort -rn | grep -v -E " (root|$USER|dbus|chrony|polkitd|rpc|munge|nobody|systemd.*|libstoragemgmt|sssd|avahi|rtkit|tss|pbsdata|postfix|nslcd|ntp|colord|gdm|nscd)$" || echo "none"
echo "## load"; uptime
echo "## pbsnodes jobs on this node"; pbsnodes "$(hostname -s)" 2>/dev/null | grep -E "jobs|resources_assigned|resources_available.ncpus|resources_available.mem|state" || pbsnodes "$(hostname)" 2>/dev/null | grep -E "jobs|resources_assigned|resources_available|state"
echo "## gpu"; nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv 2>/dev/null || echo "no nvidia-smi"
echo "## disk (home)"; df -h /home | tail -1
echo "## local scratch"; df -h /tmp /scratch 2>/dev/null
echo "## python"; /home/$USER/RAO_OCT/venv/bin/python -c "import faiss,numpy,torch,sys;print(sys.version.split()[0],'faiss',faiss.__version__,'numpy',numpy.__version__,'torch',torch.__version__,'cuda',torch.cuda.is_available())"
} > "$OUT" 2>&1
