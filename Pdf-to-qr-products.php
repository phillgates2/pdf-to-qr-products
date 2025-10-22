<?php
/*
Plugin Name: PDF to QR Products
Description: Extracts product info from PDFs, generates QR codes, saves PNGs and CSV, and displays front-end gallery.
Version: 1.0
Author: Philip
*/

define('PDF_TO_QR_DIR', plugin_dir_path(__FILE__));
define('PDF_TO_QR_URL', plugin_dir_url(__FILE__));
define('PDF_TO_QR_UPLOAD_DIR', 'pdf-to-qr-products');

require_once PDF_TO_QR_DIR . 'lib/qrlib.php';

add_action('wp_enqueue_scripts', function(){
    wp_enqueue_script('pdfjs', PDF_TO_QR_URL . 'assets/pdfjs/pdf.min.js', [], null, true);
    wp_enqueue_script('pdfjs-worker', PDF_TO_QR_URL . 'assets/pdfjs/pdf.worker.min.js', [], null, true);
    wp_enqueue_script('qrcode', PDF_TO_QR_URL . 'assets/qrcode/qrcode.min.js', [], null, true);
    wp_enqueue_script('pdf-to-qr-frontend', PDF_TO_QR_URL . 'assets/frontend.js', ['jquery','pdfjs','qrcode'], null, true);
    wp_localize_script('pdf-to-qr-frontend', 'PDF_TO_QR', [
        'ajaxUrl' => admin_url('admin-ajax.php'),
        'workerSrc' => PDF_TO_QR_URL . 'assets/pdfjs/pdf.worker.min.js'
    ]);
    wp_enqueue_style('pdf-to-qr-shortcode', PDF_TO_QR_URL . 'assets/shortcode.css');
});

add_shortcode('pdf_to_qr_upload', function(){
    if (!is_user_logged_in()) {
        $login_url = wp_login_url(get_permalink());
        return '<div class="pdf-to-qr-login-message">
                    <p>You need to be logged in to use this feature. Redirecting to login in 5 seconds…</p>
                    <p><a href="' . esc_url($login_url) . '">Click here if not redirected</a></p>
                    <script>setTimeout(function(){ window.location.href = "' . esc_url($login_url) . '"; }, 5000);</script>
                </div>';
    }

    ob_start(); ?>
    <div id="pdf-to-qr-frontend">
        <form id="pdf-to-qr-frontend-form">
            <?php wp_nonce_field('pdf_to_qr_nonce', '_wpnonce', true, true); ?>
            <input type="file" id="pdfFileFrontend" accept="application/pdf" required />
            <button type="submit">Upload PDF</button>
            <button type="button" id="saveToServerBtn" style="display:none;">Save QR PNGs + CSV to Server</button>
        </form>
        <div id="frontendStatus"></div>
        <div id="frontendResults" style="display:none;">
            <h3>Extracted Products</h3>
            <table>
                <thead>
                    <tr><th>Reference</th><th>Description</th><th>Category</th><th>QR Code</th></tr>
                </thead>
                <tbody id="frontendResultsBody"></tbody>
            </table>
        </div>
    </div>
    <?php return ob_get_clean();
});

add_action('wp_ajax_pdf_to_qr_frontend_save', function(){
    check_ajax_referer('pdf_to_qr_nonce');
    if (!is_user_logged_in()) wp_send_json_error(['message' => 'Unauthorized'], 403);

    $items = isset($_POST['items']) ? json_decode(stripslashes($_POST['items']), true) : [];
    if (!is_array($items) || empty($items)) wp_send_json_error(['message' => 'No items received.']);

    $upload = wp_upload_dir();
    $dir = trailingslashit($upload['basedir']) . PDF_TO_QR_UPLOAD_DIR;
    if (!is_dir($dir)) wp_mkdir_p($dir);

    foreach (glob($dir . '/*.png') as $f) unlink($f);
    if (file_exists($dir . '/products.csv')) unlink($dir . '/products.csv');

    foreach ($items as $it) {
        $ref = sanitize_file_name($it['reference'] ?? '');
        if (!$ref) continue;
        $pngPath = $dir . '/' . $ref . '.png';
        ob_start();
        QRcode::png($ref, null, QR_ECLEVEL_L, 6, 2);
        file_put_contents($pngPath, ob_get_clean());
    }

    $csvPath = $dir . '/products.csv';
    $fh = fopen($csvPath, 'w');
    fputcsv($fh, ['reference', 'description', 'category', 'qr_filename']);
    foreach ($items as $it) {
        $ref = sanitize_file_name($it['reference'] ?? '');
        $desc = sanitize_text_field($it['description'] ?? '');
        $cat = sanitize_text_field($it['category'] ?? '');
        if (!$ref) continue;
        fputcsv($fh, [$ref, $desc, $cat, $ref . '.png']);
    }
    fclose($fh);

    wp_send_json_success([
        'message' => 'Saved to server.',
        'csvUrl' => trailingslashit($upload['baseurl']) . PDF_TO_QR_UPLOAD_DIR . '/products.csv'
    ]);
});
