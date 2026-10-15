# Qwen Image Studio — RunPod Serverless starter

Targets `AtomicChat/Qwen-Image-2.1-Turbo-Uncensored-GGUF`, with text-to-image and image-edit modes, a small browser UI, a password-protected Cloudflare Worker proxy, and no permanent image gallery or persistent model volume.

## Important

This is a **starter implementation, not a live-tested deployment**. It must be built and smoke-tested against a RunPod GPU before relying on it. It uses `stable-diffusion.cpp` because the selected GGUF model card documents that engine and its exact 8-step Turbo schedule.

## Deploy worker

1. Create a GitHub repository and upload this project's files, preserving the folder structure. Use `main` as the default branch.
2. Under Actions, enable workflows if GitHub asks. Run **Build and publish RunPod worker**. The workflow compiles the CUDA version of `stable-diffusion.cpp` and publishes an image to GHCR. This can take several minutes.
3. Make the GHCR package public for easiest RunPod pulls, or configure registry access.
4. In https://www.runpod.io/console/serverless choose **New Endpoint → Import from Docker Registry**.
5. Set image to `ghcr.io/YOUR_GITHUB_USERNAME/qwen-image-turbo-worker:latest`, endpoint type **Queue**, min workers **0**, max workers **1**, job timeout at least **1200 seconds**, and a GPU with 24 GB VRAM for the first test.
6. Set container disk to **30 GB or more**. The required model assets are about 15 GB before runtime/cache overhead. Increase disk if a cold start runs out of space. Do not attach a network volume.
7. Deploy and copy the endpoint ID.

The worker downloads the denoiser, uncensored text encoder, vision projector, and VAE to ephemeral `/tmp` storage. A new worker may have to download them again after scaling to zero. It returns the output image as base64 and deletes temporary per-job files.

## Deploy UI

You need Node.js and Wrangler. In a terminal:

```bash
cd ui
npx wrangler deploy
```

If Wrangler asks to authenticate, log into Cloudflare first. This project uses a Worker plus static assets configured in `wrangler.toml`.

Set secrets from the `ui` folder:

```bash
npx wrangler secret put RUNPOD_API_KEY
npx wrangler secret put RUNPOD_ENDPOINT_ID
npx wrangler secret put APP_PASSWORD
```

Enter your RunPod API key, the endpoint ID, and a strong private app password when prompted. Never place the RunPod API key in `index.html`. Optionally put Cloudflare Access in front of the deployed Worker for another access layer.

## Test

Open the deployed Worker URL, enter the app password, select **Text to image**, use a simple prompt and 768×768, then click Generate. After that, test **Edit photo** with a normal test image. Download the result before closing the page.

## Cost/privacy

- Serverless can scale to zero, but cold-start downloads and generation are billed worker time.
- No persistent volume is used. Model files are kept only on the worker's ephemeral disk; after scale-to-zero they may need downloading again.
- Photos are sent as base64 through Cloudflare to RunPod for processing. Don't upload sensitive photos unless comfortable with the providers handling them.
- The app has a password gate, not user accounts. Use a strong password and consider Cloudflare Access.
- Never generate sexual content involving minors or intimate/degrading images of real people without consent.

## References

- Model card: https://huggingface.co/AtomicChat/Qwen-Image-2.1-Turbo-Uncensored-GGUF
- Turbo denoiser: https://huggingface.co/AtomicChat/Qwen-Image-2.1-Turbo-GGUF
- VAE: https://huggingface.co/Comfy-Org/Qwen-Image-2.1
- sd.cpp Qwen 2.1 usage: https://github.com/leejet/stable-diffusion.cpp/blob/master/docs/qwen_image_2.1.md
- RunPod Serverless quickstart: https://docs.runpod.io/serverless/quickstart
