import { getCsrfToken } from '../utilities/getCsrfToken.js';
import { inCanvasMode } from './taskbar.js';
import { getInputValue } from '../utilities/inputs.js';

const penSizeInput = document.querySelector('[name="pen-size"]');
const penColorInput = document.querySelector('.pen-color-picker');
const selectPenButton = document.querySelector('.select-pen');

const eraserSizeInput = document.querySelector('[name="eraser-size"]');
const selectEraserButton = document.querySelector('.select-eraser');

const textSizeInput = document.querySelector('[name="text-size"]');
const textColorInput = document.querySelector('.text-color-picker');
const selectTextButton = document.querySelector('.select-text');
const selectImageButton = document.querySelector('.select-image');

const backgroundColorInput = document.querySelector('.background-color-picker');

const shapeSelect = document.querySelector('.shape-select');
const shapeColorInput = document.querySelector('.shape-color-picker');

class Canvas {
    constructor({
        canvas,
        overlay,
        noteId,
        noteToken,
        editable,
        backgroundColor,
    }) {
        /**
         * @type {HTMLCanvasElement}
         */
        this.canvas = canvas;
        /**
         * @type {CanvasRenderingContext2D}
         */
        this.ctx = canvas.getContext('2d');
        this.noteId = noteId;
        this.noteToken = noteToken;
        this.editable = editable;

        this.overlay = overlay;

        this.overlay.width = this.canvas.width;
        this.overlay.height = this.canvas.height;
        this.overlay.style.top = this.canvas.offsetTop + 'px';
        this.overlay.style.left = this.canvas.offsetLeft + 'px';

        this.overlayCtx = this.overlay.getContext('2d');

        this.zoom = 1;

        this.backgroundColor = backgroundColor;
        this.canvas.style.backgroundColor = this.backgroundColor;

        if (editable) {
            this.penSize = parseInt(penSizeInput.value);
            this.penColor = penColorInput.querySelector('input').value;

            this.eraserSize = parseInt(eraserSizeInput.value);

            this.textSize = parseInt(textSizeInput.value);
            this.textColor = textColorInput.querySelector('input').value;

            this.shapeColor = shapeColorInput.querySelector('input').value;

            this.mouseDownHandler = null;
            this.mouseMoveHandler = null;
            this.mouseUpHandler = null;
            this.touchMoveHandler = null;

            this.history = [];
            this.historyIndex = 0;

            this.holdingShift = false;
        }

        this.registerListeners();
        this.loadInitial();
    }

    clearHandlers() {
        document.querySelector('.icon.selected')?.classList.remove('selected');

        if (this.mouseDownHandler) {
            this.canvas.removeEventListener(
                'pointerdown',
                this.mouseDownHandler,
            );
            this.mouseDownHandler = null;
        }

        if (this.mouseMoveHandler) {
            this.canvas.removeEventListener(
                'pointermove',
                this.mouseMoveHandler,
            );
            this.mouseMoveHandler = null;
        }

        if (this.mouseUpHandler) {
            this.canvas.removeEventListener('pointerup', this.mouseUpHandler);
            this.mouseUpHandler = null;
        }

        if (this.touchMoveHandler) {
            this.canvas.removeEventListener('touchmove', this.touchMoveHandler);
            this.touchMoveHandler = null;
        }
    }

    clearOverlay() {
        this.overlayCtx.clearRect(
            0,
            0,
            this.overlay.width,
            this.overlay.height,
        );
    }

    isMobile() {
        return navigator.userAgent.match(/Mobi/) !== null;
    }

    preventTouchScrolling() {
        if (!this.touchMoveHandler) {
            this.touchMoveHandler = (e) => {
                e.preventDefault();
            };

            this.canvas.addEventListener('touchmove', this.touchMoveHandler);
        }
    }

    drawCircle(x, y) {
        this.ctx.beginPath();
        this.ctx.arc(x, y, this.penSize / 2, 0, Math.PI * 2);
        this.ctx.fillStyle = this.penColor;
        this.ctx.fill();
    }

    eraseCircle(x, y) {
        this.ctx.save();

        this.ctx.beginPath();
        this.ctx.arc(x, y, this.eraserSize / 2, 0, Math.PI * 2);
        this.ctx.clip();

        this.ctx.clearRect(
            x - this.eraserSize / 2,
            y - this.eraserSize / 2,
            this.eraserSize,
            this.eraserSize,
        );

        this.ctx.restore();
    }

    interpolatePoints(x1, y1, x2, y2) {
        const points = [];
        const distance = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
        const steps = Math.ceil(distance / (this.penSize / 4));

        for (let i = 0; i <= steps; i++) {
            const t = i / steps;
            points.push({
                x: x1 + (x2 - x1) * t,
                y: y1 + (y2 - y1) * t,
            });
        }

        return points;
    }

    drawPreviewCircle(x, y, radius, color = '#000000') {
        this.overlayCtx.clearRect(
            0,
            0,
            this.overlay.width,
            this.overlay.height,
        );

        let baseStrokeWidth;

        if (radius < 4) {
            baseStrokeWidth = 1;
        } else if (radius < 12) {
            baseStrokeWidth = 2;
        } else if (radius < 32) {
            baseStrokeWidth = 3;
        } else {
            baseStrokeWidth = 4;
        }

        let strokeWidth = baseStrokeWidth / this.zoom;

        strokeWidth = Math.max(0.5, Math.min(strokeWidth, 10));

        this.overlayCtx.strokeStyle = color;
        this.overlayCtx.lineWidth = strokeWidth;
        this.overlayCtx.beginPath();
        this.overlayCtx.arc(x, y, radius, 0, Math.PI * 2);
        this.overlayCtx.stroke();
    }

    selectPen() {
        this.clearHandlers();
        this.preventTouchScrolling();

        selectPenButton.querySelector('.icon').classList.add('selected');

        let drawing = false;
        let lastX = null;
        let lastY = null;

        this.registerPointerDownHandler((e) => {
            e.preventDefault();
            drawing = true;
            lastX = e.offsetX;
            lastY = e.offsetY;
            this.drawCircle(e.offsetX, e.offsetY);
        });

        this.registerPointerMoveHandler(
            (e) => {
                this.clearOverlay();

                if (!this.isMobile()) {
                    this.drawPreviewCircle(
                        e.offsetX,
                        e.offsetY,
                        this.penSize / 2,
                        this.penColor,
                    );
                }

                if (!drawing) return;

                const currentX = e.offsetX;
                const currentY = e.offsetY;

                const points = this.interpolatePoints(
                    lastX,
                    lastY,
                    currentX,
                    currentY,
                );
                points.forEach((point) => {
                    this.drawCircle(point.x, point.y);
                });

                lastX = currentX;
                lastY = currentY;
            },
            {
                passive: true,
            },
        );

        this.registerPointerUpHandler((e) => {
            drawing = false;
            lastX = null;
            lastY = null;

            this.pushHistory();
        });
    }

    selectEraser() {
        this.clearHandlers();

        this.preventTouchScrolling();

        selectEraserButton.querySelector('.icon').classList.add('selected');

        let erasing = false;
        let lastX = null;
        let lastY = null;

        this.registerPointerDownHandler((e) => {
            e.preventDefault();

            erasing = true;
            lastX = e.offsetX;
            lastY = e.offsetY;
            this.eraseCircle(e.offsetX, e.offsetY);
        });

        this.registerPointerMoveHandler(
            (e) => {
                this.clearOverlay();

                if (!this.isMobile()) {
                    this.drawPreviewCircle(
                        e.offsetX,
                        e.offsetY,
                        this.eraserSize / 2,
                    );
                }

                if (!erasing) {
                    return;
                }

                const currentX = e.offsetX;
                const currentY = e.offsetY;

                const points = this.interpolatePoints(
                    lastX,
                    lastY,
                    currentX,
                    currentY,
                );
                points.forEach((point) => {
                    this.eraseCircle(point.x, point.y);
                });

                lastX = currentX;
                lastY = currentY;
            },
            {
                passive: true,
            },
        );

        this.registerPointerUpHandler((e) => {
            e.preventDefault();

            erasing = false;
            lastX = null;
            lastY = null;

            this.pushHistory();
        });
    }

    selectText() {
        this.clearHandlers();

        selectTextButton.querySelector('.icon').classList.add('selected');

        this.registerPointerDownHandler((e) => {
            e.preventDefault();

            const text = prompt('Enter text');
            if (text) {
                this.ctx.font = `${this.textSize}px Arial`;

                const fm = this.ctx.measureText(text);

                this.ctx.fillStyle = this.textColor;
                this.ctx.fillText(
                    text,
                    e.offsetX,
                    e.offsetY + fm.actualBoundingBoxAscent,
                );
                this.pushHistory();
            }
        });

        this.registerPointerMoveHandler((e) => {
            this.clearOverlay();

            this.overlayCtx.font = `${this.textSize}px Arial`;

            const fm = this.overlayCtx.measureText('Text');

            this.overlayCtx.fillStyle = this.textColor;
            this.overlayCtx.fillText(
                'Text',
                e.offsetX,
                e.offsetY + fm.actualBoundingBoxAscent,
            );

            this.overlay.style.cursor = 'text';
        });
    }

    selectImage() {
        this.clearHandlers();

        selectImageButton.querySelector('.icon').classList.add('selected');

        const fileInput = document.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = 'image/*';
        let image = null;

        fileInput.addEventListener('change', async () => {
            const file = fileInput.files[0];
            if (!file) {
                return;
            }

            const img = new Image();
            img.src = URL.createObjectURL(file);

            img.onload = () => {
                image = img;
            };
        });

        fileInput.click();

        this.registerPointerDownHandler((e) => {
            if (!image) {
                return;
            }

            e.preventDefault();

            this.ctx.drawImage(image, e.offsetX, e.offsetY);
            this.pushHistory();
        });

        this.registerPointerMoveHandler((e) => {
            this.clearOverlay();

            if (!image) {
                return;
            }

            this.overlayCtx.drawImage(image, e.offsetX, e.offsetY);
        });
    }

    clear() {
        if (!confirm('Are you sure you want to clear the canvas?')) {
            return;
        }
        this.clearOverlay();
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.history = [
            this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height),
        ];
        this.historyIndex = 0;
        this.save();

        const undoButton = document.querySelector('.task-bar .undo-button');
        const redoButton = document.querySelector('.task-bar .redo-button');

        undoButton.classList.add('disabled');
        redoButton.classList.add('disabled');
    }

    selectShape() {
        const shape = shapeSelect.value;

        this.clearHandlers();

        if (shape === 'rectangle') {
            this.selectRectangle();
        } else if (shape === 'circle') {
            this.selectCircle();
        } else if (shape === 'triangle') {
            this.selectTriangle();
        }
    }

    selectRectangle() {
        this.preventTouchScrolling();

        let drawing = false;
        let startX = null;
        let startY = null;

        this.registerPointerDownHandler((e) => {
            e.preventDefault();

            drawing = true;
            startX = e.offsetX;
            startY = e.offsetY;
        });

        this.registerPointerMoveHandler(
            (e) => {
                this.clearOverlay();

                if (!drawing) return;

                let width = e.offsetX - startX;
                let height = e.offsetY - startY;

                if (this.holdingShift) {
                    if (width > height) {
                        height = width;
                    } else {
                        width = height;
                    }
                }

                this.overlayCtx.fillStyle = this.shapeColor;
                this.overlayCtx.fillRect(startX, startY, width, height);
            },
            {
                passive: true,
            },
        );

        this.registerPointerUpHandler((e) => {
            if (!drawing) return;

            e.preventDefault();

            drawing = false;

            let width = e.offsetX - startX;
            let height = e.offsetY - startY;

            if (this.holdingShift) {
                if (width > height) {
                    height = width;
                } else {
                    width = height;
                }
            }

            this.ctx.fillStyle = this.shapeColor;
            this.ctx.fillRect(startX, startY, width, height);

            this.pushHistory();
        });
    }

    selectCircle() {
        this.preventTouchScrolling();

        let drawing = false;
        let startX = null;
        let startY = null;

        this.registerPointerDownHandler((e) => {
            e.preventDefault();

            drawing = true;
            startX = e.offsetX;
            startY = e.offsetY;
        });

        this.registerPointerMoveHandler(
            (e) => {
                this.clearOverlay();

                if (!drawing) return;

                const radius = Math.sqrt(
                    (e.offsetX - startX) ** 2 + (e.offsetY - startY) ** 2,
                );

                this.overlayCtx.fillStyle = this.shapeColor;
                this.overlayCtx.beginPath();
                this.overlayCtx.arc(startX, startY, radius, 0, Math.PI * 2);
                this.overlayCtx.fill();
            },
            {
                passive: true,
            },
        );

        this.registerPointerUpHandler((e) => {
            if (!drawing) return;

            e.preventDefault();

            drawing = false;

            const radius = Math.sqrt(
                (e.offsetX - startX) ** 2 + (e.offsetY - startY) ** 2,
            );

            this.ctx.fillStyle = this.shapeColor;
            this.ctx.beginPath();
            this.ctx.arc(startX, startY, radius, 0, Math.PI * 2);
            this.ctx.fill();

            this.pushHistory();
        });
    }

    selectTriangle() {
        this.preventTouchScrolling();

        let drawing = false;
        let startX = null;
        let startY = null;

        this.registerPointerDownHandler((e) => {
            e.preventDefault();

            drawing = true;
            startX = e.offsetX;
            startY = e.offsetY;
        });

        this.registerPointerMoveHandler(
            (e) => {
                this.clearOverlay();

                if (!drawing) return;

                this.overlayCtx.fillStyle = this.shapeColor;
                this.overlayCtx.beginPath();
                this.overlayCtx.moveTo(startX, startY);
                this.overlayCtx.lineTo(e.offsetX, e.offsetY);
                this.overlayCtx.lineTo(startX * 2 - e.offsetX, e.offsetY);
                this.overlayCtx.closePath();
                this.overlayCtx.fill();
            },
            {
                passive: true,
            },
        );

        this.registerPointerUpHandler((e) => {
            if (!drawing) return;

            e.preventDefault();

            drawing = false;

            this.ctx.fillStyle = this.shapeColor;
            this.ctx.beginPath();
            this.ctx.moveTo(startX, startY);
            this.ctx.lineTo(e.offsetX, e.offsetY);
            this.ctx.lineTo(startX * 2 - e.offsetX, e.offsetY);
            this.ctx.closePath();
            this.ctx.fill();

            this.pushHistory();
        });
    }

    pushHistory() {
        this.history = this.history.slice(0, this.historyIndex + 1);
        this.history.push(
            this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height),
        );
        this.historyIndex++;

        const undoButton = document.querySelector('.task-bar .undo-button');
        const redoButton = document.querySelector('.task-bar .redo-button');

        if (this.history.length <= 1) {
            undoButton.classList.add('disabled');
        } else {
            undoButton.classList.remove('disabled');
        }

        redoButton.classList.add('disabled');

        this.save();
    }

    undo() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            this.ctx.putImageData(this.history[this.historyIndex], 0, 0);

            const undoButton = document.querySelector('.task-bar .undo-button');
            const redoButton = document.querySelector('.task-bar .redo-button');

            if (this.historyIndex === 0) {
                undoButton.classList.add('disabled');
            } else {
                undoButton.classList.remove('disabled');
            }

            redoButton.classList.remove('disabled');

            this.save();
        }
    }

    redo() {
        if (this.historyIndex < this.history.length - 1) {
            this.historyIndex++;
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            this.ctx.putImageData(this.history[this.historyIndex], 0, 0);

            const undoButton = document.querySelector('.task-bar .undo-button');
            const redoButton = document.querySelector('.task-bar .redo-button');

            if (this.historyIndex === this.history.length - 1) {
                redoButton.classList.add('disabled');
            } else {
                redoButton.classList.remove('disabled');
            }

            undoButton.classList.remove('disabled');

            this.save();
        }
    }

    registerPointerDownHandler(handler, options = {}) {
        this.mouseDownHandler = handler;
        this.canvas.addEventListener('pointerdown', handler, options);
    }

    registerPointerMoveHandler(handler, options = {}) {
        let isThrottled = false;

        const throttledHandler = (event) => {
            if (isThrottled) return;

            isThrottled = true;
            const copy = {
                offsetX: event.offsetX,
                offsetY: event.offsetY,
                clientX: event.clientX,
                clientY: event.clientY,
                pageX: event.pageX,
                pageY: event.pageY,
            };

            requestAnimationFrame(() => {
                handler(copy);
                isThrottled = false;
            });
        };

        this.mouseMoveHandler = throttledHandler;
        this.canvas.addEventListener('pointermove', throttledHandler, options);
    }

    registerPointerUpHandler(handler, options = {}) {
        this.mouseUpHandler = handler;
        this.canvas.addEventListener('pointerup', handler, options);
    }

    registerListeners() {
        const taskbar = document.querySelector('.task-bar');

        if (this.editable) {
            let selected = '';

            taskbar.addEventListener('mouseover', () => {
                this.clearOverlay();
            });

            selectPenButton.addEventListener('click', () => {
                if (selected === 'pen') {
                    this.clearHandlers();
                    selected = '';
                    selectPenButton
                        .querySelector('.icon')
                        .classList.remove('selected');
                    this.clearOverlay();
                } else {
                    this.selectPen();
                    selected = 'pen';
                }
            });
            selectEraserButton.addEventListener('click', () => {
                if (selected === 'eraser') {
                    this.clearHandlers();
                    selected = '';
                    selectEraserButton
                        .querySelector('.icon')
                        .classList.remove('selected');
                    this.clearOverlay();
                } else {
                    this.selectEraser();
                    selected = 'eraser';
                }
            });
            selectTextButton.addEventListener('click', () => {
                if (selected === 'text') {
                    this.clearHandlers();
                    selected = '';
                    selectTextButton
                        .querySelector('.icon')
                        .classList.remove('selected');
                    this.clearOverlay();
                } else {
                    this.selectText();
                    selected = 'text';
                }
            });
            selectImageButton.addEventListener('click', () => {
                if (selected === 'image') {
                    this.clearHandlers();
                    selected = '';
                    selectImageButton
                        .querySelector('.icon')
                        .classList.remove('selected');
                    this.clearOverlay();
                } else {
                    selected = 'image';
                    this.selectImage();
                }
            });
            penSizeInput.addEventListener('input', () => {
                this.penSize = parseInt(penSizeInput.value);
            });
            eraserSizeInput.addEventListener('input', () => {
                this.eraserSize = parseInt(eraserSizeInput.value);
            });
            textSizeInput.addEventListener('input', () => {
                this.textSize = parseInt(textSizeInput.value);
            });

            penColorInput.addEventListener('colorchange', (e) => {
                this.penColor = e.detail.color;
            });
            textColorInput.addEventListener('colorchange', (e) => {
                this.textColor = e.detail.color;
            });
            backgroundColorInput.addEventListener('colorchange', (e) => {
                this.backgroundColor = e.detail.color;
                this.canvas.style.backgroundColor = this.backgroundColor;
                this.saveBackground();
            });
            shapeColorInput.addEventListener('colorchange', (e) => {
                this.shapeColor = e.detail.color;
            });

            shapeSelect.addEventListener('change', () => {
                this.selectShape();
            });

            document.addEventListener('keydown', (e) => {
                if (e.key === 'Shift') {
                    this.holdingShift = true;
                }
            });

            document.addEventListener('keyup', (e) => {
                if (e.key === 'Shift') {
                    this.holdingShift = false;
                }
            });

            const clearButton = taskbar.querySelector('.clear-button');
            const undoButton = taskbar.querySelector('.undo-button');
            const redoButton = taskbar.querySelector('.redo-button');

            clearButton.addEventListener('click', () => this.clear());
            undoButton.addEventListener('click', () => this.undo());
            redoButton.addEventListener('click', () => this.redo());
        }

        const zoomOutButton = taskbar.querySelector('.zoom-out-button');
        const zoomInButton = taskbar.querySelector('.zoom-in-button');

        zoomOutButton.addEventListener('click', () => {
            this.zoom *= 0.9;
            this.canvas.style.transform = `scale(${this.zoom})`;
            this.overlay.style.transform = `scale(${this.zoom})`;
        });

        zoomInButton.addEventListener('click', () => {
            this.zoom *= 1.1;
            this.canvas.style.transform = `scale(${this.zoom})`;
            this.overlay.style.transform = `scale(${this.zoom})`;
        });

        const downloadButton = taskbar.querySelector('.download-button');

        downloadButton.addEventListener('click', () => {
            if (!inCanvasMode() || this.downloading) {
                return;
            }

            this.download();
        });
    }

    async save() {
        const url = `/notes/${this.noteToken}/canvas/save`;

        const formData = new FormData();
        const blob = await new Promise((resolve) => {
            this.canvas.toBlob(resolve, 'image/png');
        });

        formData.append('file', blob);

        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
            },
            body: formData,
        });
    }

    async saveBackground() {
        const url = `/notes/${this.noteId}/canvas/background`;

        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
            },
            body: JSON.stringify({
                background: this.backgroundColor,
            }),
        });
    }

    async loadInitial() {
        const url = `/notes/${this.noteToken}/canvas`;

        const response = await fetch(url);
        const canvasLoadingIcon = document.querySelector(
            '.canvas-loading-icon',
        );

        if (!response.ok) {
            canvasLoadingIcon.classList.add('hidden');
            return;
        }

        const blob = await response.blob();

        const img = new Image();
        img.src = URL.createObjectURL(blob);

        img.onload = () => {
            this.ctx.drawImage(img, 0, 0);

            if (this.editable) {
                this.history.push(
                    this.ctx.getImageData(
                        0,
                        0,
                        this.canvas.width,
                        this.canvas.height,
                    ),
                );
            }
            canvasLoadingIcon.classList.add('hidden');
        };

        img.onerror = () => {
            canvasLoadingIcon.classList.add('hidden');
        }
    }

    download() {
        this.downloading = true;

        const taskbar = document.querySelector('.task-bar');
        const downloadButton = taskbar.querySelector('.download-button');
        const canvasOptions = taskbar.querySelector('.canvas-options');
        const exportOptions = taskbar.querySelector(
            '.export-options-container',
        );
        const exportButton = exportOptions.querySelector('.export-button');
        const cancelExportButton = exportOptions.querySelector(
            '.cancel-export-button',
        );

        for (const child of canvasOptions.children) {
            child.classList.add('hidden');
        }

        exportOptions.classList.remove('hidden');

        downloadButton.classList.add('active');
        this.clearOverlay();
        this.clearHandlers();
        this.preventTouchScrolling();

        let startX = null;
        let startY = null;
        let drawing = false;
        let selectedDataUrl = null;

        this.registerPointerDownHandler((e) => {
            e.preventDefault();

            drawing = true;

            startX = e.offsetX;
            startY = e.offsetY;
        });

        this.registerPointerMoveHandler(
            (e) => {
                if (!drawing) return;

                this.clearOverlay();

                const width = e.offsetX - startX;
                const height = e.offsetY - startY;

                this.overlayCtx.strokeStyle = '#000000';
                this.overlayCtx.lineWidth = 2;
                this.overlayCtx.strokeRect(startX, startY, width, height);
            },
            {
                passive: true,
            },
        );

        this.registerPointerUpHandler((e) => {
            e.preventDefault();

            drawing = false;

            const width = e.offsetX - startX;
            const height = e.offsetY - startY;

            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = width;
            tempCanvas.height = height;

            const tempCtx = tempCanvas.getContext('2d');

            tempCtx.fillStyle = this.backgroundColor;
            tempCtx.fillRect(0, 0, width, height);

            tempCtx.drawImage(
                this.canvas,
                startX,
                startY,
                width,
                height,
                0,
                0,
                width,
                height,
            );

            selectedDataUrl = tempCanvas.toDataURL();
        });

        const exportListener = () => {
            if (!selectedDataUrl) {
                if (!confirm('No selection. Export entire canvas?')) {
                    return;
                }

                selectedDataUrl = this.canvas.toDataURL();
            }

            const a = document.createElement('a');
            a.href = selectedDataUrl;
            a.download = (getInputValue('note-name') || 'cana') + '.png';
            a.click();
        };

        exportButton.addEventListener('click', exportListener);

        const cancelListener = () => {
            if (
                selectedDataUrl &&
                !confirm('Are you sure you want to cancel?')
            ) {
                return;
            }

            this.clearHandlers();
            this.clearOverlay();
            downloadButton.classList.remove('active');

            for (const child of canvasOptions.children) {
                child.classList.remove('hidden');
            }

            exportOptions.classList.add('hidden');

            cancelExportButton.removeEventListener('click', cancelListener);
            exportButton.removeEventListener('click', exportListener);

            this.downloading = false;
        };

        cancelExportButton.addEventListener('click', cancelListener);
    }
}

export { Canvas };
