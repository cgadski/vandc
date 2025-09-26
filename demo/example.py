import torch
import vandc
import argparse


def run(args):
    torch.manual_seed(args.seed)
    x = torch.randn(args.d)

    value = x.pow(2).sum()

    for _ in vandc.progress(range(args.iters)):
        upd = args.beta * torch.randn(args.d)
        new_value = (x + upd).pow(2).sum()
        if new_value < value:
            value = new_value
            x = x + upd
        vandc.log({"value": value})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--d", type=int, required=True)
    parser.add_argument("--beta", type=float, required=True)
    parser.add_argument("--iters", type=int, default=1000)
    args = parser.parse_args()

    vandc.init(args)
    run(args)
    vandc.close()
